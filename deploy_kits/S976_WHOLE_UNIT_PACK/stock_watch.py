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

VERSION = "1.15"                                                    # v1.15 S969: every morning list reaches Darpan's phone (F-1712) · v1.14 S958: his next-list asks every morning; his counts pushed to Darpan · v1.13 S957: the recount match keeps a same-day bill S956 adds after a morning count · v1.12 S952_RECORD_JUDGES (D1065): every count judged against the one record
KIT = "S936_RECOUNT_SITTING"                                        # v1.11 S936 (a count short by a fresh delivery held for a recount; one bill per sitting), v1.10 S934 (Count now, placed to the bill), v1.9 S928 (the bill over the tap; the day's count line), v1.8 S587_MORNING_FLOW, v1.7 was S584_SMALL_FIXES, v1.6 S583_ARRIVALS_ONE_RULE, v1.5 S577_STOCK_ON_SPINE
# v1.8 (S587, 18-Oct-2026, D740): two settings under "Counts & watch" -- count.start_capture (the start-of-day closing on / off) and
# count.start_unexplained_max (items that may change with no Marg reason before such a closing is set aside); stock_figure reads them through
# settings(); needs_you_lines gains start_capture_lines (the set-aside / waiting start captures of the last 7 days, English).
# v1.7 (S584, 18-Oct-2026): nine settings reach the owner's card under the heading "Amir and the reports" (amir.proof_wait_hours,
# amir.refused_keep_hours, amir.job_wait_days, amir.salt_owed_days, amir.self_exports, amir.claim_open_days, amir.voucher_visits,
# owner.salt_list_days, owner.item_lists_days) -- rows with no default of their own: _default(s) reads amir_day.S444_DEFAULTS /
# reports_tile.OWNER_LISTS (one default, one place); the hints are amir_day.S444_NOTES. PREFIXES gains "amir." and "owner." so the desk's
# save door (stock_app /api/loss/<cid>/pile/setting) hands them here. set_setting keeps a row's existing note (the S444 note survives a save).
# v1.6 (S583, 18-Oct-2026): ONE rule for "Marg carries this arrival" -- stock_figure.carried (a: the line's own Marg bill; b: a bill that answered
# another line of the key never; c: the own vendor's bill up to arrival.back_days before the order day; d: the own vendor's bill on or after it;
# e: another supplier's bill on or after it) and stock_figure.expired (the spine's purchase reach past the arrival + arrival.bill_grace_days,
# ISO against ISO). _arrivals' in_spine = carried() is not None, nothing else; bill_pending_lines tests carried(); the owner's Needs-you gains
# arrival_needs_you (an expired scan-tied arrival; the untied taps stay with amir_day._d712_owner_lines). New setting arrival.back_days (no row).
# v1.5 (S577, rung 4b, 18-Oct-2026): a spot count is judged by stock_figure.expect_for_point -- the shelf figure (counted), Marg's figure
# (uncounted), or NO figure for a size that shares a family figure (basis 'approx': the plain receipt only, no verdict, no loss line, no
# trace, out of the month's leakage). stock_point.basis (additive) carries it; settle_provisional re-judges a provisional point on its stored
# basis; a correction keeps the old point's basis; open_trace judges its window on the same base. _arrivals and bill_pending_lines key the
# spine by stock_figure.key_of (charter 12). expected_units stays for the witness week only; the unread close-day method of Spine is gone.
# v1.4 (S502, D699, 10-Oct-2026; F-812, F-813, F-814, F-815): a morning-list count can be corrected the same day (correct_roster -- the old
# point superseded, never deleted; the new one judged on the OLD expected figure); a loss line can be VOIDED (void_at / void_why, F-814) and a
# voided line shows nowhere; superseded points are skipped where points are picked or summed; Darpan's page shows the last 7 days' loss lines
# in plain words. The 06-Sep count is sealed for staff (stockmatch.api_recount). THE LAST PATCH on this layer under the S303 build charter.
# v1.3 (S436, D638, 28-Sep-2026): the Needs-you list carries the 'ortho_closed' notice (stockmatch.close_by_rule writes it: "Orthotics
# closed: N lines short, Rs X at selling price; round R on Amir's board"); the stored watch's time no longer reads "IST IST".
# v1.2 (S432, F-651, 28-Sep-2026): the traces and the watch scoring LEAVE THE DESK'S READ PATH. owner_view() is computed by the
# 06:30 job and by 'Refresh watch' (refresh_owner_view) and STORED (stock_watch_view); the desk shows the stored view with its
# time (stored_owner_view -- built once on the very first read if nothing is stored yet). A Big-loss trace is opened by the
# close / the clear (trace_big_losses from stock_app), never by reading the desk.
# v1.1 (S430, D637 / F-650, 27-Sep-2026): a closed count's write-off is leakage of the PERIOD between the previous closed count (or
# the opening) and that count -- one line for the period in the Month section, spread pro rata by each month's sales only for the
# cadence and the red-period rule; the watch list leaves out the orthotic section and costly items with no sale in 90 days unless
# MRP >= spot.dead_high_value_p; a trace whose anchor is the count itself ends 'first_count', not 'unexplained', in one collapsed line.
OPENING_DAY = "2026-04-01"
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
SPINE_DB = os.environ.get("SPINE_DB") or os.path.join(HERE, "spine", "spine.db")
DAYS = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")
SOURCES = ("full_count", "spot", "darpan", "sales_test", "receipt")
POINT_SOURCE_HI = {"full_count": "poori ginti", "spot": "subah ki ginti", "darpan": "Darpan ne bataya", "sales_test": "bikri se saabit", "receipt": "maal aaya"}

S584_HEADING = "Amir and the reports"                        # S584: the second heading of the owner's card; the first is "Counts & watch"
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
    dict(key="count.start_capture", label="Start-of-day closing: use a closing printed today and taken before the first sale", kind="choice", default="1", seed=None,
         choices=(("1", "on"), ("0", "off")),                 # S587 (D740)
         hint="A closing stock printed as on today and taken before the day's first sale counts as the START of that day (the end of yesterday plus the "
              "morning's Marg work) once the system has verified it item by item against that day's sale report and Amir's purchase export. Off = the old rule "
              "(such a closing is never used)."),
    dict(key="count.start_unexplained_max", label="Start-of-day closing: items that may change with no Marg reason before it is set aside", kind="int", default="3",
         seed=None, lo=0, hi=50,                               # S587 (D740)
         hint="Items whose Marg figure moved between the previous verified closing and the start-of-day closing with no reason the system knows (a count "
              "voucher, Amir's correction, the consumption list, a purchase of the day). More than this many sets the closing aside; a drop no bigger than "
              "the day's sales sets it aside at once (a sale came before it)."),
    dict(key="spot.days", label="Spot counts: mornings", kind="days", default="MON,WED,SAT", seed="MON,WED,SAT",
         hint="The mornings Darpan gets 'Aaj ki ginti' -- three a week, not a daily chore."),
    dict(key="spot.cap", label="Spot counts: items a morning", kind="int", default="2", seed="2", lo=0, hi=20,
         hint="At most this many items in one sitting. 0 = off. The owner's own asks come first and are never dropped."),
    dict(key="spot.watch_size", label="Close-watch list: items", kind="int", default="20", seed="20", lo=5, hi=100,
         hint="The watch list on your desk: the top items by sales value, the costly ones, and items short at two closed counts."),
    dict(key="spot.high_value_p", label="Costly item: MRP per strip / pc", kind="rupees", default="50000", seed="50000",
         hint="An item whose MRP per strip or piece is this or more scores as costly and joins the watch list."),
    dict(key="spot.dead_high_value_p", label="Costly item with no sale in 90 days: keep on the watch from (MRP)", kind="rupees", default="200000", seed="200000",
         hint="A costly item that has not sold in 90 days stays on the watch list only from this MRP per strip / pc (Bonista PF, the Bonmax pen stay; "
              "cast shoes and belts go). The orthotic section never joins the list -- it has its own cycle."),
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
    dict(key="arrival.back_days", label="Arrival: a bill dated before the order (days)", kind="int", default="2", seed=None, lo=0, hi=15,
         hint="The order's own supplier's bill dated up to this many days BEFORE the order day still answers that order's arrival (the goods came "
              "before the order was written up). 0 = only bills dated on or after the order day."),
    dict(key="arrival.bill_over_tap", label="Arrival: the scanned bill over the tap", kind="choice", default="1", seed="1", choices=(("1", "on"), ("0", "off")),
         hint="S928, the owner 22-Nov: a delivery counts by the quantity the dealer's scanned bill carries for the medicine, never by reception's tap -- a tap above the bill "
              "is a short supply (back on that dealer's next order), a tapped medicine the bill does not carry counts nothing. Off: the tap stands, as before."),
    dict(key="count.recount_tol_pct", label="Recount: a count short by about a fresh delivery (tolerance, % of the delivery)", kind="pct", default="25", seed=None,
         lo=5, hi=50,                                          # S936 (D1046)
         hint="S936, the owner 23-Nov: a count short of the expected figure by about a delivery received in the days before it is more likely a missed "
              "carton than a loss -- it is HELD for a recount (not the shelf figure, no loss line, nothing on the order list) and put on Darpan's Count now "
              "with the question whether that carton was on the shelf. 'About' = the shortfall within this share of the delivery."),
    dict(key="count.recount_days", label="Recount: a delivery counts as fresh for (days)", kind="int", default="5", seed=None, lo=1, hi=15,
         hint="S936: a delivery tapped, scanned or dated within this many days before a count is a fresh delivery for the recount rule."),
    dict(key="count.sitting_minutes", label="Count now: one bill number for a sitting of (minutes)", kind="int", default="60", seed=None, lo=5, hi=240,
         hint="S936, the owner 23-Nov: Darpan keys the last sale bill once for a sitting; an item he saves within this many minutes of his last "
              "Count now with a bill takes that bill unless he taps 'Sale hui?' for a new one."),
    dict(key="count.evening_hour", label="Count: the evening hour (a count at or after it ends its day)", kind="int", default="17", seed="17", lo=0, hi=23,
         hint="S928 (F-1564): a count saved on its own day at or after this hour stands for the END of that day -- its day's sales are not taken off again. "
              "Darpan's morning list is before it; an evening count (TYRO BR, 12-Oct 19:49) is after it."),
    dict(key="leak.budget_pct", label="Leakage budget (% of sales)", kind="pct", default="1.0", seed="1.0", lo=0, hi=100,
         hint="A month's loss points + count write-offs (allowance, small, big -- not consumption) at cost, against the month's sales. Over the budget is red."),
    dict(key="leak.red_periods", label="Leakage: red months running -> Needs you", kind="int", default="2", seed="2", lo=1, hi=12,
         hint="This many red months in a row puts one line on your Needs you."),
    # S584: the nine rows below carry NO default and NO hint of their own -- _default(s) / _hint(s) read the module that owns the figure
    dict(key="amir.proof_wait_hours", label="Voucher proof: hours before your warn line", kind="int", seed=None, lo=1, hi=240,
         heading=S584_HEADING, default_from=("amir_day", "amir.proof_wait_hours")),
    dict(key="amir.refused_keep_hours", label="Refused report: hours on your Needs-you list", kind="int", seed=None, lo=1, hi=168,
         heading=S584_HEADING, default_from=("amir_day", "amir.refused_keep_hours")),
    dict(key="amir.job_wait_days", label="Amir's one-time Marg jobs: days before your line", kind="int", seed=None, lo=1, hi=60,
         heading=S584_HEADING, default_from=("amir_day", "amir.job_wait_days")),
    dict(key="amir.salt_owed_days", label="Salt list: visits owed before your line", kind="int", seed=None, lo=1, hi=30,
         heading=S584_HEADING, default_from=("amir_day", "amir.salt_owed_days")),
    dict(key="amir.self_exports", label="Amir's own correction: bill-wise exports before your line", kind="int", seed=None, lo=1, hi=10,
         heading=S584_HEADING, default_from=("amir_day", "amir.self_exports")),
    dict(key="amir.claim_open_days", label="A claim for Darpan: days open before your line", kind="int", seed=None, lo=1, hi=60,
         heading=S584_HEADING, default_from=("amir_day", "amir.claim_open_days")),
    dict(key="amir.voucher_visits", label="Count vouchers untouched: Amir's visits before your line", kind="int", seed=None, lo=1, hi=10,
         heading=S584_HEADING, default_from=("amir_day", "amir.voucher_visits")),
    dict(key="owner.salt_list_days", label="Your salt-wise list: overdue after (days)", kind="int", seed=None, lo=1, hi=60,
         heading=S584_HEADING, default_from=("reports_tile", "owner.salt_list_days"),
         hint="Marg's salt-wise item list counts as overdue on your Reports card after this many days without a fresh one."),
    dict(key="owner.item_lists_days", label="Your category and item lists: overdue after (days)", kind="int", seed=None, lo=1, hi=120,
         heading=S584_HEADING, default_from=("reports_tile", "owner.item_lists_days"),
         hint="Marg's category-wise list and item master count as overdue on your Reports card after this many days without a fresh one."),
)
SETTING_BY_KEY = {s["key"]: s for s in SETTINGS}
PREFIXES = ("count.", "spot.", "arrival.", "leak.", "amir.", "owner.")   # S584: the desk's save door routes these prefixes here


def _default(s):
    """S584: ONE default per setting. A row's own `default`, else the module that owns the figure: amir_day.S444_DEFAULTS[key], or the [2]
    of the reports_tile.OWNER_LISTS triple whose type maps to the key in reports_tile.S488_LIST_KEYS (two types share owner.item_lists_days
    and carry the same limit -- asserted). Lazy imports: amir_day imports this file lazily, reports_tile is stdlib + flask -- no cycle."""
    if "default" in s:
        return s["default"]
    mod, key = s["default_from"]
    if mod == "amir_day":
        import amir_day                                        # noqa: PLC0415
        return str(amir_day.S444_DEFAULTS[key])
    import reports_tile                                       # noqa: PLC0415
    vals = {int(t[2]) for t in reports_tile.OWNER_LISTS if reports_tile.S488_LIST_KEYS.get(t[0]) == key}
    assert len(vals) == 1, "reports_tile.OWNER_LISTS: %s has %d limits" % (key, len(vals))
    return str(vals.pop())


def _hint(s):
    """S584: the row's hint -- its own, else amir_day.S444_NOTES[key] (read, not copied)."""
    if "hint" in s:
        return s["hint"]
    import amir_day                                            # noqa: PLC0415
    return amir_day.S444_NOTES[s["default_from"][1]]

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
  at TEXT NOT NULL, item TEXT NOT NULL, gap_units REAL NOT NULL, pack INTEGER, packing TEXT, mrp_p INTEGER, point_id INTEGER,
  void_at TEXT, void_why TEXT                -- S502 (F-814): a line the system no longer believes -- voided, never deleted
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
CREATE TABLE IF NOT EXISTS stock_watch_view (
  key TEXT PRIMARY KEY,                    -- S432: the owner's watch card as last computed ('owner')
  root INTEGER, made_at TEXT NOT NULL, made_by TEXT, ms INTEGER, traces_n INTEGER, json TEXT NOT NULL
);
"""
_TABLES = ("stock_point", "stock_count_plan", "stock_spot_roster", "stock_watch_ask", "stock_trace", "stock_watch_loss_line",
           "stock_watch_notice", "stock_watch_adjust", "stock_watch_view")
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


def _sf():
    import stock_figure                                       # noqa: PLC0415 -- beside this file: THE one stock function (S577); it imports this file lazily
    return stock_figure


_UNSET = object()                                          # S502: 'not given' for write_point(expected=) -- None already means "work it out fresh"


def _s502_columns(con):
    """S502 (F-814): void_at / void_why on stock_watch_loss_line -- added on EVERY call to a database whose tables already exist
    (ensure()'s own branch runs only when a table is missing). A voided line is one the system no longer believes; it is never deleted."""
    try:
        cols = {r[1] for r in con.execute("PRAGMA table_info(stock_watch_loss_line)").fetchall()}
        for c in ("void_at", "void_why"):
            if cols and c not in cols:
                con.execute("ALTER TABLE stock_watch_loss_line ADD COLUMN %s TEXT" % c)
    except sqlite3.Error:
        pass


def _s577_columns(con):
    """S577: stock_point.basis -- 'shelf' | 'marg' | 'approx' (what the point was judged against; NULL on older rows = 'marg'). Additive."""
    try:
        cols = {r[1] for r in con.execute("PRAGMA table_info(stock_point)").fetchall()}
        if cols and "basis" not in cols:
            con.execute("ALTER TABLE stock_point ADD COLUMN basis TEXT")
    except sqlite3.Error:
        pass


def ensure(con):
    have = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN (%s)" % ",".join("?" * len(_TABLES)), _TABLES)}
    if len(have) < len(_TABLES):
        con.executescript(SCHEMA)
    _s502_columns(con)
    _s577_columns(con)
    _s934_columns(con)
    _s936_columns(con)


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
        out[s["key"]] = raw if raw is not None else _default(s)   # S584: a row without a default of its own reads its module's

    def num(k, d, f=float):
        try:
            return f(float(out[k]))
        except (TypeError, ValueError):
            return d
    days = [d.strip().upper()[:3] for d in str(out["spot.days"]).split(",") if d.strip()]
    return dict(raw=out, cadence_months=max(0.5, num("count.cadence_months", 2.0)), window_sundays=max(1, num("count.window_sundays", 4, int)),
                auto_adjust=str(out["count.auto_adjust"]).strip() not in ("0", "off", "no"), good_pct=num("count.good_pct", 1.0), bad_pct=num("count.bad_pct", 2.0),
                spot_days=[d for d in days if d in DAYS], cap=max(0, num("spot.cap", 2, int)), watch_size=max(1, num("spot.watch_size", 20, int)),
                high_value_p=max(0, num("spot.high_value_p", 50000, int)), dead_high_value_p=max(0, num("spot.dead_high_value_p", 200000, int)),
                repeat_gap_days=max(0, num("spot.repeat_gap_days", 7, int)),
                arrival_days=max(1, num("spot.arrival_days", 3, int)),
                weights=dict(turnover=num("spot.w_turnover", 3, int), movement=num("spot.w_movement", 2, int), arrival=num("spot.w_arrival", 3, int),
                             loss=num("spot.w_loss", 3, int), value=num("spot.w_value", 1, int), stale=num("spot.w_stale", 2, int)),
                bill_grace_days=max(1, num("arrival.bill_grace_days", 3, int)), back_days=max(0, num("arrival.back_days", 2, int)),
                bill_over_tap=str(out.get("arrival.bill_over_tap", "1")).strip() not in ("0", "off", "no"),          # S928: stock_figure reads these two
                evening_hour=max(0, min(23, num("count.evening_hour", 17, int))),
                recount_tol_pct=max(5.0, min(50.0, num("count.recount_tol_pct", 25.0))),            # S936 (D1046)
                recount_days=max(1, min(15, num("count.recount_days", 5, int))),
                sitting_minutes=max(5, min(240, num("count.sitting_minutes", 60, int))),             # S936 (D1047)
                budget_pct=num("leak.budget_pct", 1.0), red_periods=max(1, num("leak.red_periods", 2, int)),
                start_capture=str(out["count.start_capture"]).strip() not in ("0", "off", "no"),            # S587 (D740): stock_figure reads these two
                start_unexplained_max=max(0, num("count.start_unexplained_max", 3, int)))


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
        v = raw if raw is not None else _default(s)
        rows.append(dict(key=s["key"], label=s["label"], kind=s["kind"], value=v, shown=_shown(s, v), hint=_hint(s),
                         choices=[dict(v=a, t=b) for a, b in s.get("choices", ())], set=(raw is not None),
                         rupees=(None if s["kind"] != "rupees" else int(float(v)) // 100), heading=s.get("heading") or "Counts & watch"))   # S584
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
    con.execute("INSERT INTO setting (key, value, note) VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, "
                "note=COALESCE(NULLIF(note,''), excluded.note)",   # S584: a row's own note (the S444 seed's) survives a save
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

    def sales(self, name, d_from, d_to, incl_from=False):
        op = ">=" if incl_from else ">"
        # S454 P3B (18.5, F-713): a credit note (bill CN...) carries positive units -- it is a RETURN: u = sales net of returns, ret = returns
        r = self.q("SELECT COALESCE(SUM(CASE WHEN UPPER(COALESCE(bill,'')) LIKE 'CN%%' THEN -units ELSE units END),0) AS u, "
                   "COALESCE(SUM(CASE WHEN UPPER(COALESCE(bill,'')) LIKE 'CN%%' THEN units WHEN units<0 THEN -units ELSE 0 END),0) AS ret, "
                   "COALESCE(SUM((CASE WHEN UPPER(COALESCE(bill,'')) LIKE 'CN%%' THEN -1 ELSE 1 END)*rate_p*units/NULLIF(CASE WHEN pack LIKE '1*%%' THEN CAST(substr(pack,3) AS REAL) ELSE 1 END,0)),0) AS v, "
                   "COALESCE(SUM(CASE WHEN UPPER(COALESCE(bill,'')) LIKE 'CN%%' THEN 0 ELSE 1 END),0) AS n, "
                   "COALESCE(SUM(CASE WHEN qty_raw LIKE '0:%%' AND NOT (UPPER(COALESCE(bill,'')) LIKE 'CN%%') THEN units ELSE 0 END),0) AS loose "
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
        r = con.execute("SELECT item, packing, pack_size FROM stock_snapshot WHERE item=? ORDER BY substr(as_on,7,4)||substr(as_on,4,2)||substr(as_on,1,2) DESC LIMIT 1", (name,)).fetchone()
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
def _tie_sql(con):
    """The order's scan moment as a column ('' when the tie table is not there)."""
    try:
        if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='order_scan_tie'").fetchone():
            return "(SELECT MAX(t.scan_at) FROM order_scan_tie t WHERE t.order_id=o.id AND t.arrived=1)"
    except sqlite3.Error:
        pass
    return "NULL"


def _arrivals(con, item, since_iso, sp, ctx=None):
    """Tapped arrivals of the item after since_iso (purchase_order_line, supplied packs x pack_size) with the supplier, each marked
    in_spine = stock_figure.carried(line) is not None -- THE one rule (S583, charter 2: rules a-e live in stock_figure) and nothing else: expiry
    is applied by stock_figure.taps / scan_arrivals, so open_trace's finding 2 and Amir's 'bill entry baaki' fix keep seeing a tap Marg never
    carried. scan_at = the order's scan moment ('' when untied); billed_date beside billed_bill_no. S577: the spine is keyed by
    stock_figure.key_of (a renamed item reaches its family's purchases); the order line is still matched by pad_norm(name[:27]) -- seen, not
    touched (charter 12)."""
    out = []
    try:
        keys = {pad_norm(item[:27]), pad_norm(item)}
        for r in con.execute("SELECT l.id, l.item, l.packs, l.pack_size, l.supplied, l.arrived_at, l.arrived_by, l.billed_qty, l.billed_bill_no, o.vendor, o.created_at, o.id, "
                             "l.billed_date, " + _tie_sql(con) + " FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                             "WHERE l.arrived_at IS NOT NULL AND l.arrived_at>? AND l.supplied>0", (since_iso,)):
            if pad_norm(str(r[1])[:27]) not in keys and pad_norm(r[1]) not in keys:
                continue
            a = dict(line_id=r[0], item=r[1], packs=int(r[2] or 0), pack_size=int(r[3] or 1), supplied=int(r[4] or 0), units=float(r[4] or 0) * float(r[3] or 1),
                     arrived_at=r[5], arrived_by=r[6] or "", billed_qty=r[7], billed_bill_no=r[8] or "", billed_date=r[12] or "", vendor=r[9] or "", supkey=supkey(r[9]),
                     order_id=r[11], order_at=r[10], scan_at=str(r[13] or ""), kind="tap", in_spine=False)
            a["in_spine"] = _sf().carried(con, sp, a, ctx) is not None
            out.append(a)
    except sqlite3.Error:
        pass
    return out


def expected_units(con, sp, item):
    """WITNESS ONLY (S577, rung 4b-2 retires it): the old expectation -- the latest sp_close (printed day = day end, no capture rule) -
    sales since + purchases since (net of returns) + PROVISIONAL tapped arrivals. Read by stock_figure.witness beside stock_figure.marg for
    one week; no judgment reads it any more (expect_for_point is the one)."""
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
    q += " AND status NOT IN ('superseded','recount','recounted')"   # S502: a replaced count is never picked; S936: nor a count held for a recount
    r = con.execute(q + " ORDER BY at DESC, id DESC LIMIT 1", (item_norm,)).fetchone()
    return dict(id=r[0], at=r[1], qty=r[2], expected=r[3], gap=r[4], status=r[5], source=r[6], by=r[7]) if r else None


def write_point(con, item, qty_units, source, who, roster_id=None, note=None, sp=None, count_id=None, silent=False,
                expected=_UNSET, expected_as_on=None, commit=True, basis=None, hold=True):
    """ONE stock point: expected from stock_figure.expect_for_point (the shelf figure for a counted item, Marg's figure for an uncounted
    one; provisional if an arrival is provisional), the gap, and what follows -- a short within the item's allowance is a quiet loss point;
    a larger one is a dated loss line under the staff block and on the owner's watch card; a surplus is noted. Returns the point row.
    S577 (R2-B8): a size that shares a FAMILY figure (basis 'approx') stores NULL expected and NULL gap -- no verdict, no loss line, no trace;
    the staff receipt alone. A correction (expected given) carries the OLD point's basis."""
    ensure(con)
    sp = sp or Spine()
    info = item_info(con, sp, item)
    item = info["item"]
    rc = _s936_open_recount_ask(con, item)                    # S936 (D1046): this count answers the item's open recount -- and is never held itself
    if rc is not None:
        hold = False
    if expected is _UNSET:
        E = _s952_judge(con, sp, item, now_iso(), qty_units, live=True) or _s454_expected(con, sp, item)   # S952: the one record; else S577's
    else:                                                      # S502 (F-812): a correction is judged against the figure the old point was judged on
        E = dict(expected=(None if (expected is None or basis == "approx") else float(expected)), provisional=0.0,
                 as_on=(str(expected_as_on)[:10] if expected_as_on else None), basis=(basis or ("marg" if expected is not None else None)))
    basis = E.get("basis")
    ts = now_iso()
    gap = None if E["expected"] is None else round(float(qty_units) - E["expected"], 3)
    status = "provisional" if E["provisional"] else "settled"
    cur = con.execute("INSERT INTO stock_point (item_norm, item, at, qty_units, source, by, expected_units, gap_units, status, settled_at, note, count_id, roster_id, provisional_units, basis) "
                      "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      (norm_name(item), item, ts, float(qty_units), source, who or "", E["expected"], gap, status, (ts if status == "settled" else None), note, count_id, roster_id, E["provisional"], basis))
    pid = int(cur.lastrowid)
    if E.get("words"):                                         # S952: the judgment's own words, for the owner's Stock check page
        _s952_words(con, pid, E["words"])
    if rc is not None:
        _s936_close_recount(con, rc, pid, ts, who)            # S936: the held count it answers -- 'recounted', any line of it voided
    P = dict(id=pid, item=item, pack=info["pack"], packing=info["packing"], qty=float(qty_units), expected=E["expected"], gap=gap, status=status, provisional=E["provisional"],
             qty_text=qw(qty_units, info["pack"], info["packing"], item), qty_hi=qw(qty_units, info["pack"], info["packing"], item, "hi"),
             gap_text=("" if gap is None else qw(abs(gap), info["pack"], info["packing"], item)), gap_hi=("" if gap is None else qw(abs(gap), info["pack"], info["packing"], item, "hi")),
             verdict="", verdict_hi="", loss_line=None, trace=None, basis=basis, expected_as_on=E.get("as_on"))
    if basis == "approx":
        P["verdict"], P["verdict_hi"] = "", ""                 # S577: counted against a family figure -- not judged; the receipt alone (R3 blocker 2)
    elif gap is None and E.get("awaits"):                      # S952: an evening count is judged to its day's end, when that day's sale report is in
        con.execute("UPDATE stock_point SET status='awaits_sales', settled_at=NULL, expected_units=NULL, gap_units=NULL WHERE id=?", (pid,))
        P.update(status="awaits_sales", verdict="counted in the evening -- judged to the day's end when that day's sale report is in",
                 verdict_hi="Shaam ki ginti -- kal ki sale report aane par milaan hoga.")
    elif gap is None:
        P["verdict"], P["verdict_hi"] = "no Marg figure for this item yet -- counted and kept", "Marg mein yeh item nahi mila -- ginti likh li"
    elif gap == 0:
        P["verdict"], P["verdict_hi"] = "matches the records", "Marg se barabar"
    elif gap > 0:
        P["verdict"], P["verdict_hi"] = "%s more than the records -- noted, never a loss" % P["gap_text"], "%s zyada -- likh liya" % P["gap_hi"]
    else:
        H = _s936_match(con, sp, item, ts, -gap, info["pack"], pid) if (hold and basis in ("shelf", "marg", "record")) else None   # S936 (D1046); S952 'record'
        lp = last_point(con, norm_name(item))
        since = (lp["at"][:10] if lp and lp["id"] != pid else (E["as_on"] or (today() - dt.timedelta(days=30)).isoformat()))
        allow, sold = allowance_units(con, item, info["pack"], since, sp)
        if E.get("allowance") is not None:                      # S952: the judgment's own allowance -- its words and its verdict agree
            allow = E["allowance"]
        if H is not None and abs(gap) > allow:                 # S936: short by about a fresh delivery -- HELD for a recount: no base, no loss line, no trace
            _s936_hold_row(con, pid, H, note)
            P.update(status="recount", hold=H)
            _s952_words(con, pid, "short by about a fresh delivery (%s) -- held for a recount, not a loss" % H.get("what", ""))   # S952: the words agree
            P["verdict"] = "%s short -- about %s: held for a recount, not a loss" % (P["gap_text"], H["what"])
            P["verdict_hi"] = "%s kam -- %s shayad gina nahi gaya. Dobara ginti 'Abhi ginti' mein aayegi." % (P["gap_hi"], H["what_hi"])
            _s936_open_recount(con, P, who)                    # in the same transaction as the held count (the review, finding 8)
        elif E.get("never_loss") and abs(gap) > allow:         # S952: the figure cannot be told exactly here (the words say why) -- shown, never a loss
            P["verdict"], P["verdict_hi"] = "%s short -- noted, not a loss (the records are checked)" % P["gap_text"], "%s kam -- likh liya" % P["gap_hi"]
        elif abs(gap) <= allow:
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
                    P["trace"] = open_trace(con, item, "point", gap, who, sp=sp, point_id=pid, E=E)["id"]   # S577: the trace on the point's own base
                except Exception:                             # noqa: BLE001
                    P["trace"] = None
    P["answered_recount"] = rc[0] if rc is not None else None   # S936
    _audit(con, "point", dict(item=item, qty=float(qty_units), source=source, expected=E["expected"], gap=gap, status=P.get("status") or status, basis=basis, text="%s: %s counted (%s), %s" % (item, P["qty_text"], source, P["verdict"] or "counted against a family figure -- not judged")), who, pid)
    if commit:                                                 # S502: correct_roster commits its one transaction itself
        con.commit()
    return P


def settle_provisional(con, sp=None):
    """A provisional point whose arrival the spine now carries is re-judged ON ITS STORED BASIS (S577: stock_figure.expect_for_point with
    basis='shelf' | 'marg'; NULL = 'marg', the old meaning read through the one capture rule) and settled. An approx point is never
    re-judged. Idempotent."""
    ensure(con)
    sp = sp or Spine()
    ctx = _sf().Ctx(con, sp)
    n = 0
    for r in con.execute("SELECT id, item, qty_units, basis, at FROM stock_point WHERE status='provisional'").fetchall():
        b = str(r[3] or "marg")
        if b == "approx":
            continue
        E = _s952_judge(con, sp, r[1], r[4], r[2], exclude_id=r[0], ctx=ctx)      # S952: the one record at the point's own moment
        if E is not None and not E.get("awaits"):
            b = E.get("basis") or b
            if E.get("words"):
                _s952_words(con, r[0], E["words"])
        else:
            E = _sf().expect_for_point(con, sp, r[1], ctx=ctx, basis=b, exclude_id=r[0])   # judged against the base BEFORE the point itself
        if E["provisional"]:
            continue
        gap = None if E["expected"] is None else round(float(r[2]) - E["expected"], 3)
        con.execute("UPDATE stock_point SET expected_units=?, gap_units=?, status='settled', settled_at=?, provisional_units=0, basis=? WHERE id=?",
                    (E["expected"], gap, now_iso(), b, r[0]))
        n += 1
    if n:
        con.commit()
    _s934_settle(con, sp)                                      # S934: the Count-now points whose day's sales are in
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
    """A tapped arrival with no purchase in the spine after arrival.bill_grace_days -> Amir's line 'bill entry baaki'. S583: 'no purchase in the
    spine' = stock_figure.carried() is None (the one rule); the routing, the words and the grace are as they were."""
    S = S or settings(con)
    sp = sp or Spine()
    out = []
    cutoff = (dt.datetime.now() - dt.timedelta(days=S["bill_grace_days"])).replace(microsecond=0).isoformat()
    try:                                                      # S537: an arrival tied to its bill (billed_bill_no, from Marg's own purchase lines) is never "bill missing"
        rows = con.execute("SELECT l.item, l.supplied, l.pack_size, l.arrived_at, o.vendor, o.created_at, l.id FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                           "WHERE l.arrived_at IS NOT NULL AND l.arrived_at<? AND l.supplied>0 AND COALESCE(l.billed_bill_no,'') = '' ORDER BY l.arrived_at", (cutoff,)).fetchall()
    except sqlite3.Error:
        return out
    seen = set()
    ctx = _sf().Ctx(con, sp)                                   # S577 (F-873): the spine keyed by the one identity -- a renamed item reaches its purchases
    for item, supplied, ps, arrived, vendor, created, lid in rows:
        if not sp.ok:
            break
        sk = supkey(vendor)
        if _sf().carried(con, sp, dict(line_id=lid, item=item, vendor=vendor, order_at=created, arrived_at=arrived, billed_bill_no=""), ctx) is not None:
            continue                                           # S583: THE one rule (stock_figure.carried)
        key = (sk, str(arrived)[:10])
        if key in seen:
            continue
        seen.add(key)
        out.append(dict(vendor=vendor or "", date=str(arrived)[:10], date_text=dmy(str(arrived)[:10]), item=item,
                        text_hi="bill entry baaki: %s %s" % (vendor or "", dmy(str(arrived)[:10])), text="bill entry pending: %s, arrival tapped %s" % (vendor or "", dmy(str(arrived)[:10]))))
    return out


def arrival_needs_you(con, sp=None):
    """S583: the owner's Needs-you line for an arrival that EXPIRED (stock_figure.arrivals_open: counted as arrived, never carried by Marg's
    purchases, the spine's purchase reach past it by arrival.bill_grace_days) -- ONLY a line whose order has a scan tie (order_scan_tie); a
    tapped line on an untied order stays with amir_day._d712_owner_lines (D712), so no arrival is said twice. English, one line each. Fail-soft.
    S598 (F-942): where the family's bill carried OTHER sizes of the item (arrivals_open's family_bill), the line says so -- ' (its bill N of
    dd-mm carried SIZE, SIZE, not this size)', the sizes as Marg printed them; the clause is built here, once, and nowhere else (charter 8)."""
    out = []
    try:
        sp = sp or Spine()
        if not sp.ok:
            return out
        SF = _sf()
        ctx = SF.Ctx(con, sp)
        upto = dmy(str((SF.reach(sp) or {}).get("last_pur") or "")[:10])[:5]
        for a in SF.arrivals_open(con, sp, ctx):
            if not a.get("scan_tied"):
                continue
            when = "%s %s" % (dmy(str(a["at"])[:10])[:5], str(a["at"])[11:16])
            fb = a.get("family_bill") or {}
            more = (" (its bill %s of %s carried %s, not this size)" % (fb.get("bill") or "", dmy(str(fb.get("date") or "")[:10])[:5], ", ".join(fb.get("sizes") or []))) if fb else ""
            if a.get("kind") == "scan":
                text = "%s: counted as arrived when the %s bill was scanned %s -- not in Marg's purchases up to %s%s" % (a["item"], a["vendor"] or "supplier's", when, upto, more)
            else:
                text = "%s: counted as arrived when %s tapped it %s (%s) -- not in Marg's purchases up to %s%s" % (a["item"], a["who"] or "staff", when, a["vendor"] or "-", upto, more)
            out.append(dict(cls="warn", target="porders", text=text, panel="arrived", ref=int(a.get("line_id") or 0), since=str(a.get("at") or "")[:10]))   # S927: the Hub's inline panel
    except Exception:                                         # noqa: BLE001
        return out
    return out


def _s603_newest(sp):
    """S603: ('dd-mm hh:mm' bill-wise, 'dd-mm hh:mm' item-wise) -- the newest purchase export stamp of each family, read as purchase_cover's
    clause (b) reads them (stock_figure.purchase_cover_how: sp_export ok=1 per family); 'none yet' when absent."""
    SF = _sf()

    def dm(stamp):
        s = SF.stamp_iso(stamp)
        return ("%s-%s %s" % (s[8:10], s[5:7], s[11:16])) if s else "none yet"
    try:
        b = str((sp.q("SELECT MAX(stamp) AS s FROM sp_export WHERE ok=1 AND family='PURCHASE_BILLWISE'") or [{"s": ""}])[0]["s"] or "")
        i = str((sp.q("SELECT MAX(stamp) AS s FROM sp_export WHERE ok=1 AND family IN ('PURCHASE_ITEMWISE','PURCHASE_BILLITEMWISE')") or [{"s": ""}])[0]["s"] or "")
    except Exception:                                         # noqa: BLE001
        b, i = "", ""
    return dm(b), dm(i)


def start_capture_lines(con, sp=None):
    """S587 (D740, §3.1): the owner's English lines for the start-of-day closings (stock_figure's record stock_start_capture): one per capture
    SET ASIDE in the last 7 days, naming the items that decided it by their printed names; one for a capture still PENDING whose day's sale
    report has landed and which no purchase export covers yet (S603: stock_figure.purchase_cover_how over the capture as the judge builds it,
    end_day from the row, a read-only Ctx -- F-953; the line names the newest export of each family). Nobody is asked to re-print; Darpan and
    Shavez see nothing. Fail-soft."""
    out = []
    try:
        if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='stock_start_capture'").fetchone():
            return out
        sp = sp or Spine()
        SF = _sf()
        lo = (today() - dt.timedelta(days=7)).isoformat()
        R = SF.reach(sp) if sp.ok else {}
        for md5, as_on, si, end_day, verdict, reason, detail in con.execute("SELECT md5, as_on, stamp_iso, end_day, verdict, reason, detail FROM stock_start_capture WHERE as_on>=? ORDER BY stamp_iso", (lo,)):
            when = "%s %s" % (dmy(str(as_on))[:5], str(si or "")[11:16])
            try:
                d = json.loads(detail or "{}")
            except ValueError:
                d = {}
            if verdict == "set_aside":
                if reason == "sale_before":
                    names = ", ".join(str(x[1]) for x in (d.get("sale_before") or [])[:6])
                    out.append(dict(cls="warn", target="stock", text="Closing stock printed %s set aside — a sale came before it (%s)" % (when, names)))
                else:
                    un = d.get("unexplained") or []
                    out.append(dict(cls="warn", target="stock", text="Closing stock printed %s set aside — %d items changed with no Marg reason (%s)"
                                    % (when, len(un), ", ".join(str(x[1]) for x in un[:6]))))
            elif verdict == "pending" and R and str(R.get("last_sale") or "") >= str(as_on):
                # S603 (R1-B4): the capture as start_ready builds it -- the spine's dict with end_day from the row (a pending start capture's own
                # dict carries none) -- judged by the one rule, purchase_cover_how; a read-only Ctx (F-953). No line once an export covers it.
                ctx = SF.Ctx(con, sp, read_only=True)
                c = dict(SF.capture_of(sp, md5, ctx) or {}, md5=md5, end_day=end_day, stamp_iso=si)
                if not c.get("stamp"):
                    c["stamp"] = str(si or "")[:19].replace("-", "").replace(":", "").replace("T", "-")
                how = SF.purchase_cover_how(con, sp, c, R, ctx)
                if how is None:
                    nb, ni = _s603_newest(sp)
                    out.append(dict(cls="info", target="stock", text="Closing stock printed %s waits for a purchase export taken after it (newest: bill-wise %s, item-wise %s)"
                                    % (when, nb, ni)))
    except Exception:                                         # noqa: BLE001
        return out
    return out


# ------------------------------------------------------------------ 3.3 the roster
def _s958_asks_waiting(con):
    """S958: the owner's next-list asks not yet on a roster (his word 26-Nov 10:24: they reach Darpan the next morning, every day)."""
    try:
        return int(con.execute("SELECT COUNT(*) FROM stock_watch_ask WHERE done_at IS NULL AND roster_id IS NULL AND COALESCE(mode,'next')<>'now'").fetchone()[0] or 0)
    except sqlite3.Error:
        return 0


def _s958_push(con, title, body, url, tag="count"):
    """S958: one push to Darpan's phone (setting count.push_to, 'darpan' to start) -- the same Web Push the order notices use
    (order_rules._push; ORDER_PUSH_STUB for a walk). Fail-soft: (sent, failed)."""
    try:
        r = con.execute("SELECT value FROM setting WHERE key='count.push_to'").fetchone()
        to = [x.strip().lower() for x in str((r[0] if r and r[0] is not None else "darpan")).split(",") if x.strip()]
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        import order_rules as _OR                              # noqa: PLC0415 -- beside this file
        import time as _t                                      # noqa: PLC0415
        payload = dict(kind="count", title=title, body=body, url=url, tag=tag, ttl=21600, renotify=True, ts=int(_t.time() * 1000))
        import threading as _th                                # noqa: PLC0415
        res = []

        def _go():
            for u in to:
                try:
                    res.append(_OR._push(u, payload))
                except Exception:                             # noqa: BLE001
                    res.append((0, 1))
        th = _th.Thread(target=_go, daemon=True)
        th.start()
        th.join(8)                                            # the review: a slow push never holds a page past 8 s
        s = sum(int(a or 0) for a, _b in list(res))
        f = sum(int(b or 0) for _a, b in list(res))
        _audit(con, "s958_push", dict(to=to, body=body, sent=s, failed=f), "system")
        return s, f
    except Exception:                                         # noqa: BLE001 -- a count is never refused for a push
        return 0, 0


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
    for r in sp.q("SELECT k20, COALESCE(SUM(CASE WHEN UPPER(COALESCE(bill,'')) LIKE 'CN%' THEN -units ELSE units END),0) AS u, "     # S454 P3B (18.5): a credit note is a return
                  "COALESCE(SUM(CASE WHEN qty_raw LIKE '0:%' AND NOT (UPPER(COALESCE(bill,'')) LIKE 'CN%') THEN units ELSE 0 END),0) AS loose, "
                  "COALESCE(SUM((CASE WHEN UPPER(COALESCE(bill,'')) LIKE 'CN%' THEN -1 ELSE 1 END)*rate_p*units/NULLIF(CASE WHEN pack LIKE '1*%' THEN CAST(substr(pack,3) AS REAL) ELSE 1 END,0)),0) AS v "
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
    gctx = _sf().Ctx(con, sp)                                  # S577: one context for the roster's gap-flag reads
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
                      loss=short_last.get(nm, 0), value=1 if (mrp and mrp >= S["high_value_p"]) else 0, mrp_p=mrp, stale=since_days, last_point=lp, gap=_s454_gap_flag(con, nm, gctx))
    return out


def _rank_scores(cands, S):
    """Weighted rank-sum: each metric ranked high-to-low (ties share), scaled to [0, 1], times its weight."""
    W = S["weights"]
    keys = ("turnover", "movement", "arrival", "loss", "value", "stale", "gap")     # S454 P3 (9.3): the shelf figure and Marg moved apart
    ks = list(cands)
    n = max(1, len(ks))
    score = {k: 0.0 for k in ks}
    for m in keys:
        if not (W.get(m) if m != "gap" else W.get(m, 3)):
            continue
        order = sorted(ks, key=lambda k: -float(cands[k].get(m) or 0))
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and cands[order[j + 1]].get(m) == cands[order[i]].get(m):
                j += 1
            val = 1.0 - (i + j) / 2.0 / n if float(cands[order[i]].get(m) or 0) > 0 else 0.0
            for k in order[i:j + 1]:
                score[k] += (W.get(m) if m != "gap" else W.get(m, 3)) * val
            i = j + 1
    return score


def _reasons(c, S):
    en, hi = [], []
    if c.get("gap"):                                           # S454 P3 (9.3)
        en.append("the shelf figure and Marg moved apart"); hi.append("Marg aur shelf mein fark badla")
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


def build_roster(con, day=None, S=None, sp=None, who="system", force=False, asks_ok=False):
    """The day's roster: the owner's asks first, then yesterday's unanswered (carried), then the ranked items up to the
    cap; nothing counted within repeat_gap_days unless asked; a seeded tie-break so two runs agree. Written once per day."""
    ensure(con)
    S = S or settings(con)
    sp = sp or Spine()
    d = day or today()
    diso = d.isoformat()
    if con.execute("SELECT COUNT(*) FROM stock_spot_roster WHERE day=?", (diso,)).fetchone()[0] and not force:
        return roster_view(con, d, S, sp)
    asks_only = False
    if not force and not _spot_day(S, d):
        if not (asks_ok and _s958_asks_waiting(con)):         # S958: only the morning job (and the install) write his asks-only morning;
            return roster_view(con, d, S, sp)                 # a page opened in the afternoon never does -- they go on tomorrow's list
        asks_only = True                                      # S958: not a spot morning -- only his asks, nothing ranked, nothing carried
    ts = now_iso()
    chosen = []
    # 1 -- the owner's asks
    for r in con.execute("SELECT id, item FROM stock_watch_ask WHERE done_at IS NULL AND roster_id IS NULL AND COALESCE(mode,'next')<>'now' ORDER BY id").fetchall():   # S934: a Count now is never the morning list's
        info = item_info(con, sp, r[1])
        chosen.append(dict(item=info["item"], pack=info["pack"], packing=info["packing"], reason="you asked for it", reason_hi="Doctor sahab ne kaha", ask_id=r[0], carried=0))
    # 2 -- carried from the last roster day (unanswered)
    prev = next(((r[0],) for r in con.execute("SELECT DISTINCT day FROM stock_spot_roster WHERE day<? ORDER BY day DESC LIMIT 30", (diso,))
                 if _spot_day(S, dt.date.fromisoformat(str(r[0])[:10]))), None)   # S958 (the review): carried from the last SPOT morning
    if prev:                                                  # S958 (second look): every unanswered row since the last spot morning
        for r in con.execute("SELECT item, pack, packing, reason, reason_hi FROM stock_spot_roster WHERE day>=? AND day<? AND answered_at IS NULL ORDER BY day, rank", (prev[0], diso)).fetchall():
            if asks_only and not str(r[3] or "").startswith("you asked for it"):
                continue                                      # an asks-only morning carries only his asks; the spot items wait for the next spot morning
            if not any(x["item"] == r[0] for x in chosen):
                chosen.append(dict(item=r[0], pack=r[1], packing=r[2], reason=(r[3] or "") + " · carried from %s" % dmy(prev[0]), reason_hi=(r[4] or "") + " · %s se baaki" % dmy(prev[0]), ask_id=None, carried=1))
    # 3 -- the ranked items
    cap = S["cap"]
    if cap > 0 and sp.ok and not asks_only:
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
    mine = [x["item"] for x in chosen if x.get("ask_id")]
    if mine:                                                  # S958: his asks on today's list -- one push to Darpan
        _s958_push(con, "\u0906\u091c \u0915\u0940 \u0917\u093f\u0928\u0924\u0940", "\u0921\u0949\u0915\u094d\u091f\u0930 \u0938\u093e\u0939\u092c \u0928\u0947 \u0915\u0939\u093e: " + ", ".join(mine[:6]),
                   "/finance/stockmatch", tag="count_list")
        con.commit()
    elif chosen and str(setting_raw(con, "count.push_every_list") or "1").strip() not in ("0", "off", "no"):   # S969 (F-1712): a spot morning's list too
        _s958_push(con, "\u0906\u091c \u0915\u0940 \u0917\u093f\u0928\u0924\u0940", "%d \u0906\u0907\u091f\u092e \u0917\u093f\u0928\u0928\u0947 \u0939\u0948\u0902: " % len(chosen) + ", ".join(x["item"] for x in chosen[:6]),
                   "/finance/stockmatch", tag="count_list")
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
        x["can_fix"] = bool(x["answered_at"]) and str(x["day"])[:10] == today().isoformat()     # S502 (D699): 'Galat likha? Badlo' the same day
        x["by"] = ""
        if x["point_id"]:
            p = con.execute("SELECT gap_units, status, note, by FROM stock_point WHERE id=?", (x["point_id"],)).fetchone()
            x["gap"] = p[0] if p else None
            x["by"] = (p[3] or "") if p else ""
    return dict(day=d.isoformat(), day_text=dmy(d.isoformat()), is_spot_day=_spot_day(S, d), items=rows, open=sum(1 for x in rows if not x["answered_at"]), cap=S["cap"])


def next_roster_day(S, d=None, con=None):
    d = d or today()
    if con is not None and _s958_asks_waiting(con):           # S958: his asks go on the next morning's list, every day
        return d + dt.timedelta(days=1)
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
    for r in con.execute("SELECT item FROM stock_watch_ask WHERE done_at IS NULL AND roster_id IS NULL AND COALESCE(mode,'next')<>'now' ORDER BY id"):   # S934
        out.append(dict(item=r[0], reason="you asked for it"))
    if S["cap"] > 0 and sp.ok and _spot_day(S, day):          # S958: a morning that is not a spot day holds only his asks
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
        return True, "Pehle hi likha hai — badalna ho to 'Galat likha? Badlo' dabaiye.", 200, None     # S502
    P = write_point(con, r[1], qty_units, "spot", who, roster_id=r[0], sp=sp)
    con.execute("UPDATE stock_spot_roster SET answered_at=?, qty_units=?, point_id=? WHERE id=?", (now_iso(), float(qty_units), P["id"], r[0]))
    _s894_asked_back(con, r[1], qty_units, sp)              # S894: before the roster_id close below, which misses a carried row
    _s928_count_day(con, sp)                                 # S928: the day's one line on his Needs-you
    con.execute("UPDATE stock_watch_ask SET done_at=? WHERE roster_id=? AND done_at IS NULL AND recount_of IS NULL", (now_iso(), r[0]))   # S936: a fresh recount stays
    _s936_open_recount(con, P, who)                            # S936: idempotent (write_point opened it)
    con.commit()
    return True, ("Likh liya: %s — %s. %s" % (r[1], P["qty_hi"], P["verdict_hi"])).rstrip(), 200, P     # S577: an approx point has no verdict -- the receipt alone


def correct_roster(con, roster_id, qty_units, who, is_owner=False, sp=None):
    """S502 (D699, F-812) -- 'Galat likha? Badlo': a morning-list count corrected THE SAME DAY by the one who wrote it (or the owner).
    A count is never lost, only replaced: the old point is marked superseded (its note names the replacement) and a NEW point takes
    its place, judged against the figure the OLD point was judged on (its own expected_units -- never a fresh shelf figure, which
    would take the wrong old point itself as the base and book a false loss). The old point's loss line is voided, its open trace
    closed BY ITS OWN ID. Every path returns four values (ok, msg, code, P), the shape of answer_roster; refusals carry P=None."""
    r = con.execute("SELECT id, item, day, answered_at, qty_units, point_id FROM stock_spot_roster WHERE id=?", (int(roster_id),)).fetchone()
    if not r or not r[3] or not r[5]:
        return False, "Yeh ginti abhi likhi nahi gayi.", 404, None
    if str(r[2])[:10] != today().isoformat():
        return False, "Sirf aaj ki ginti badal sakte hain.", 409, None
    old = con.execute("SELECT id, item, qty_units, expected_units, at, by, note, basis FROM stock_point WHERE id=?", (int(r[5]),)).fetchone()
    if not old:
        return False, "Yeh ginti abhi likhi nahi gayi.", 404, None
    if (old[5] or "") != (who or "") and not is_owner:
        return False, "Yeh ginti kisi aur ne likhi thi — doctor sahab se kahiye.", 403, None
    q = float(qty_units)
    if q == float(r[4] if r[4] is not None else old[2]):
        return True, "Wahi ginti pehle se likhi hai.", 200, None
    sp = sp or Spine()
    info = item_info(con, sp, old[1])
    old_words = qw(old[2], info["pack"], info["packing"], old[1], "hi")
    ts = now_iso()
    try:
        _s936_withdraw_for(con, old[0], who)                   # S936: a recount asked about the old count is not this correction's to answer
        rf = _s936_recount_for(con, old[0])                    # S936 (the review, finding 2): the old count answered a recount -- its correction is never held
        con.execute("UPDATE stock_point SET status='superseded' WHERE id=?", (old[0],))
        P = write_point(con, old[1], q, "spot", who, roster_id=r[0], note="badla: pehle %s likha tha (point %d)" % (old_words, old[0]), sp=sp,
                        expected=old[3], expected_as_on=str(old[4] or "")[:10], commit=False, silent=True, hold=(rf is None), basis=(old[7] or ("marg" if old[3] is not None else None)))   # S577: the old point's basis, approx included
        con.execute("UPDATE stock_point SET note=? WHERE id=?", (((old[6] + " · ") if old[6] else "") + "S502: badla, ab point %d" % P["id"], old[0]))
        con.execute("UPDATE stock_watch_loss_line SET void_at=?, void_why='ginti badli' WHERE point_id=? AND void_at IS NULL", (ts, old[0]))
        con.execute("UPDATE stock_trace SET status='seen', seen_by='S502', seen_at=? WHERE status='open' AND json_extract(findings_json,'$.point_id')=?", (ts, old[0]))
        con.execute("UPDATE stock_spot_roster SET qty_units=?, point_id=?, answered_at=? WHERE id=?", (q, P["id"], ts, r[0]))
        if rf is not None:
            con.execute("UPDATE stock_point SET recount_for=? WHERE id=?", (rf, P["id"]))
        _s936_open_recount(con, P, who)                        # S936: idempotent
        _audit(con, "spot_fix", dict(item=old[1], old_qty=float(old[2]), new_qty=q, old_point=old[0], new_point=P["id"]), who, P["id"])
        con.commit()
        _s894_refix(con, old[1], q, sp)                         # S894
        _s928_count_day(con, sp)                             # S928: the day's line follows the corrected count
    except Exception:                                         # noqa: BLE001 -- nothing half-written
        try:
            con.rollback()
        except Exception:                                     # noqa: BLE001
            pass
        return False, "Nahi hua, dobara koshish kijiye.", 500, None
    if P.get("loss_line"):                                    # still short beyond the allowance against the old expected figure: its trace, as write_point would have
        try:
            P["trace"] = open_trace(con, old[1], "point", P["gap"], who, sp=sp, point_id=P["id"], E=dict(basis=P.get("basis"), as_on=P.get("expected_as_on"), expected=P.get("expected")))["id"]
        except Exception:                                     # noqa: BLE001 -- the correction stands; the trace is a courtesy
            P["trace"] = None
    return True, ("Badal diya: %s — %s. %s" % (old[1], P["qty_hi"], P["verdict_hi"])).rstrip(), 200, P


def _s894_text(con, item, qty_units, sp=None):
    """S894: the owner's line for an asked count, against Marg's newest closing (by its date, as item_info reads it)."""
    info = item_info(con, sp or Spine(), item)
    name = info.get("item") or item
    pack, packing = int(info.get("pack") or 1), info.get("packing") or ""
    q = float(qty_units)
    txt = "Darpan counted %s (you asked): %s" % (name, qw(q, pack, packing, name))
    snap = con.execute("SELECT qty, as_on FROM stock_snapshot WHERE item=? ORDER BY substr(as_on,7,4)||substr(as_on,4,2)||substr(as_on,1,2) DESC, rowid DESC LIMIT 1",
                       (name,)).fetchone()
    if snap and snap[0] is not None:
        m = float(snap[0])
        d = q - m
        txt += " -- Marg (closing %s) %s" % (snap[1], qw(m, pack, packing, name))
        txt += " -- matches Marg" if abs(d) < 0.5 else " -- %s %s than Marg" % (qw(abs(d), pack, packing, name), "fewer" if d < 0 else "more")
    else:
        txt += " -- Marg's figure not read"
    return txt


def _s894_asked_back(con, item, qty_units, sp=None):
    """S894 (20-Nov-2026, the owner's word 14:44): a count the owner ASKED for ('Count this') reaches his Needs-you the moment it is
    entered, beside Marg's own closing figure, and every open ask for that item closes -- also when the answer came on a later day's
    list (a carried roster row), which never closed the ask before (asks 3 and 4 of 14-Nov). One line per item per day. The line is
    written FIRST, the ask closed after it (a failed line never leaves a closed ask with no word). Fail-soft: the count itself is
    already stored and is never held up by this."""
    try:
        nm = norm_name(item)
        if not con.execute("SELECT 1 FROM stock_watch_ask WHERE item_norm=? AND done_at IS NULL AND recount_of IS NULL", (nm,)).fetchone():   # S936
            return None
        try:
            txt = _s894_text(con, item, qty_units, sp)
        except Exception:                                     # noqa: BLE001 -- the plain line, never none
            txt = "Darpan counted %s (you asked): %s units -- see the stock page" % (item, qty_units)
        notice(con, "asked_count", "owner", txt, once_key="asked:%s:%s" % (nm, today().isoformat()), days=7)
        con.execute("UPDATE stock_watch_ask SET done_at=? WHERE item_norm=? AND done_at IS NULL AND recount_of IS NULL", (now_iso(), nm))   # S936
        return txt
    except Exception:                                         # noqa: BLE001
        return None


def _s894_refix(con, item, qty_units, sp=None):
    """S894: 'Galat likha? Badlo' on an asked item the same day -- the owner's line follows the corrected count. Fail-soft."""
    try:
        key = "asked:%s:%s" % (norm_name(item), today().isoformat())
        if con.execute("SELECT 1 FROM stock_watch_notice WHERE kind='asked_count' AND once_key=?", (key,)).fetchone():
            con.execute("UPDATE stock_watch_notice SET text=? WHERE kind='asked_count' AND once_key=?",
                        (_s894_text(con, item, qty_units, sp) + " (corrected)", key))
            con.commit()
    except Exception:                                         # noqa: BLE001
        pass


# ------------------------------------------------------------------ S928 (D1037, 22-Nov-2026): every count reaches the owner -- one line a day
def _s928_cls(n):
    """The Needs-you class of a stock notice: information for a close/ortho line, a count that matches, and a day of counts with nothing below
    the records; a warning otherwise."""
    t = n.get("text") or ""
    if n.get("kind") in ("close_watch", "ortho_closed") or "matches Marg" in t:
        return "info"
    if n.get("kind") == "count_day" and "below the records" not in t:
        return "info"
    return "warn"


def _s928_count_day(con, sp=None, day=None):
    """S928 (the owner's word on mock-up v5, 22-Nov 07:49): every count Darpan writes reaches him -- ONE line per day on his Needs-you,
    'Darpan counted N items today: ...', each item with its words against the records (the figure the point was judged on: the shelf figure
    for a counted item, Marg's for an uncounted one), rewritten after every count or correction of the day (notice kind count_day, once_key
    counted:<day>). A superseded point is never read. Fail-soft: the count itself is already stored and is never held up by this."""
    try:
        d = str(day or today().isoformat())[:10]            # S934: the day of a point judged later
        rows = con.execute("SELECT item, qty_units, expected_units, gap_units, basis, by, status FROM stock_point WHERE substr(at,1,10)=? AND source IN ('spot','darpan') "
                           "AND COALESCE(status,'')<>'superseded' ORDER BY at, id", (d,)).fetchall()
        if not rows:
            return None
        sp = sp or Spine()
        parts, whos = [], []
        for item, q, _e, g, basis, by, st_ in rows:
            info = item_info(con, sp, item)
            pack, packing = int(info.get("pack") or 1), info.get("packing") or ""
            name = info.get("item") or item
            if st_ == "recount":                               # S936 (D1046)
                w = "%s -- short by about a fresh delivery, held for a recount (not a loss)" % qw(float(q), pack, packing, name)
            elif st_ == "recounted":
                w = "%s -- was held, recounted since" % qw(float(q), pack, packing, name)
            elif st_ == "awaits_sales":                          # S934: placed to the bill, judged when the day's sale report is in
                w = "%s (judged to the bill when that day's sale report is in)" % qw(float(q), pack, packing, name)
            elif basis == "approx" or g is None:
                w = "%s (no figure of its own to judge it)" % qw(float(q), pack, packing, name)
            elif abs(float(g)) < 0.5:
                w = "matches the records"
            elif float(g) < 0:
                w = "%s below the records" % qw(abs(float(g)), pack, packing, name)
            else:
                w = "%s above the records" % qw(float(g), pack, packing, name)
            parts.append("%s %s" % (name, w))
            if by and by not in whos:
                whos.append(by)
        who = " and ".join(str(x).strip().title() for x in whos) or "Darpan"
        txt = "%s counted %d item%s on %s: %s" % (who, len(rows), "" if len(rows) == 1 else "s", dmy(d), " · ".join(parts))
        key = "counted:%s" % d
        con.execute("DELETE FROM stock_watch_notice WHERE kind='count_day' AND once_key=?", (key,))   # rewritten as the day's newest line (notices read newest id first)
        notice(con, "count_day", "owner", txt, once_key=key, days=7)
        con.commit()
        return txt
    except Exception:                                         # noqa: BLE001
        return None


def ask(con, item, who, sp=None, mode=None):
    """The owner's 'Count this'. S934: mode 'now' -> Darpan's screen at once ('Abhi ginti', with the last sale bill number); 'next' -> the
    head of the next morning roster, as before. An open ask of the other mode is moved (a rostered row not yet counted leaves its list).
    mode None (an older caller, e.g. the Loss desk's Count this) -> 'next' for a new ask, and an open ask is never moved."""
    ensure(con)
    sp = sp or Spine()
    given = str(mode or "").strip().lower()
    mode = "now" if given == "now" else "next"
    info = item_info(con, sp, item)
    if not info["item"]:
        return False, "Name the item.", 400
    nm = norm_name(info["item"])
    if _s936_open_recount_ask(con, info["item"]) is not None:   # S936 (review 2, note 7): a recount stays on Abhi ginti with its question
        return True, "%s is already on Darpan's screen (a recount the system asked for)." % info["item"], 200
    r = con.execute("SELECT id, COALESCE(mode,'next'), roster_id, at FROM stock_watch_ask WHERE item_norm=? AND done_at IS NULL ORDER BY id LIMIT 1", (nm,)).fetchone()
    if r and (r[1] == mode or given not in ("now", "next")):
        return True, ("%s is already on Darpan's screen (Count now)." if r[1] == "now" else "%s is already on the next list.") % info["item"], 200
    if r:
        _s934_unroster(con, info["item"], who, r[0], r[3])
        con.execute("UPDATE stock_watch_ask SET mode=?, roster_id=NULL WHERE id=?", (mode, r[0]))
        _audit(con, "ask_mode", dict(item=info["item"], mode=mode), who, r[0])
    else:
        con.execute("INSERT INTO stock_watch_ask (item_norm, item, by, at, mode) VALUES (?,?,?,?,?)", (nm, info["item"], who, now_iso(), mode))
        _audit(con, "ask", dict(item=info["item"], mode=mode), who)
    con.commit()
    if mode == "now":                                         # S958: the count reaches his phone, the tap opens his count screen
        s, _f = _s958_push(con, "\u0905\u092d\u0940 \u0917\u093f\u0928\u0924\u0940", "\u0921\u0949\u0915\u094d\u091f\u0930 \u0938\u093e\u0939\u092c: " + info["item"] + " \u0905\u092d\u0940 \u0917\u093f\u0928\u093f\u090f (\u0906\u0916\u093c\u093f\u0930\u0940 \u092c\u093f\u0932 \u0928\u0902\u092c\u0930 \u0915\u0947 \u0938\u093e\u0925)",
                            "/finance/stockmatch", tag="count_now")
        con.commit()
        return True, "%s is on Darpan's screen now -- he counts it today with the last bill number%s." % (info["item"], " (sent to his phone)" if s else ""), 200
    return True, "%s goes at the head of Darpan's list tomorrow morning." % info["item"], 200


def darpan_point(con, item, qty_units, who, sp=None):
    """'Stock batao' -- any item, any day: a darpan point, counted like a spot answer."""
    sp = sp or Spine()
    info = item_info(con, sp, item)
    if not (sp.ok and sp.item(item)) and not con.execute("SELECT 1 FROM stock_snapshot WHERE item=? LIMIT 1", (item,)).fetchone():
        return False, "Yeh item nahi mila.", 404, None
    P = write_point(con, info["item"], qty_units, "darpan", who, sp=sp)
    _s894_asked_back(con, info["item"], qty_units, sp)       # S894
    _s928_count_day(con, sp)                                 # S928
    con.execute("UPDATE stock_watch_ask SET done_at=? WHERE item_norm=? AND done_at IS NULL AND recount_of IS NULL", (now_iso(), norm_name(info["item"])))   # S936
    _s936_open_recount(con, P, who)                            # S936: idempotent (write_point opened it)
    con.commit()
    return True, ("Likh liya: %s — %s. %s" % (info["item"], P["qty_hi"], P["verdict_hi"])).rstrip(), 200, P


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
        P = write_point(con, info["item"], qty_units, "darpan", who, note="gadbad: " + t, sp=sp, silent=True, hold=False)   # S936: his flag is never held
        gap = P["gap"]
        if P.get("basis") == "approx":                        # S577: a family figure -- the text is kept on the point; no trace, no "wajah mil gayi"
            return True, "Likh liya: %s — %s." % (info["item"], P["qty_hi"]), 200, dict(point=P, trace=None)
    else:
        gap = None
    T = open_trace(con, info["item"], "darpan", gap, who, sp=sp, note=t, point_id=(P["id"] if P else None),
                   E=(dict(basis=P.get("basis"), as_on=P.get("expected_as_on"), expected=P.get("expected")) if P else None))
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


def open_trace(con, item, trigger, gap_units, who, sp=None, note=None, point_id=None, count_id=None, quiet=False, E=None):
    """Rebuild from the anchor (the last settled point with gap 0, else the last closed full count) to now and run the
    seven checks in order; each explains the gap exactly, in part, or is ruled out. Verdict explained / partly /
    unexplained. The fix is one line for Amir. Unexplained -> Needs you the same day.
    S577: E is the point's own judgment (basis, as_on, expected -- from write_point); the window starts no earlier than that base, so the
    gap is traced on the figure it was measured against. Without E the point's basis is read from stock_figure.expect_for_point."""
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
    if E is None:
        try:
            E = _sf().expect_for_point(con, sp, item)
        except Exception:                                     # noqa: BLE001
            E = {}
    basis, basis_day = (E or {}).get("basis"), str((E or {}).get("as_on") or "")[:10]
    if basis in ("shelf", "marg", "record") and basis_day and basis_day > w_from:   # S952: 'record' -- Marg's figure at the count's moment
        w_from = basis_day                                    # S577: the window starts at the base the point was judged on
        anchor_text += "; judged on the %s of %s" % ("shelf figure" if basis == "shelf" else "Marg figure", dmy(basis_day))
    gap = None if gap_units is None else float(gap_units)
    if gap is None:
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
    elif explained > 0 or mist:
        verdict = "partly"
    elif not anchor:
        verdict = "first_count"                                # S430 (2.7): the anchor is the count itself -- no earlier point to measure from
    else:
        verdict = "unexplained"
    window_to = t
    fix = dict(lines=fixes, for_amir=(fixes[0] if fixes else ""))
    ts = now_iso()
    cur = con.execute("INSERT INTO stock_trace (item_norm, item, opened_at, trigger, anchor_at, window_from, window_to, gap_units, verdict, findings_json, fix_json, status, count_id, pack, packing) "
                      "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      (nm, item, ts, trigger, anchor_at, w_from, window_to, gap, verdict, json.dumps(dict(anchor=anchor_text, findings=findings, sales=float(sales["u"] or 0), returns=float(sales.get("ret") or 0),
                                                                                                        purchases=sum(float(p["units"] or 0) for p in purch if p["direction"] != "RETURN"), note=note or "", point_id=point_id,
                                                                                                        basis=basis, basis_day=basis_day or None)),
                       json.dumps(fix), "open", count_id, pack, packing))
    tid = int(cur.lastrowid)
    if not (verdict == "first_count" and quiet):              # S430: the count's own lines are logged once by the caller, not one line each
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
                verdict=r[8], verdict_text={"explained": "explained", "partly": "partly explained", "unexplained": "unexplained", "first_count": "no earlier point -- first count"}.get(r[8], r[8]),
                verdict_hi={"explained": "wajah mil gayi", "partly": "aadhi wajah mili", "unexplained": "wajah nahi mili", "first_count": "pehli ginti -- pehle ka koi point nahi"}.get(r[8], r[8]),
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
        n, first = 0, []
        for l in lines:
            if l.get("bucket") != "bigloss" or norm_name(l["item"]) in done:
                continue
            T = open_trace(con, l["item"], "big_loss", -float(l.get("short_units") or 0), who, sp=sp, count_id=root, quiet=True)
            if T and T["verdict"] == "first_count":
                first.append(l["item"])
            n += 1
            if n >= 40:
                break
        if first:                                              # S430: ONE log line for the count's own lines, not one per item
            _audit(con, "trace_first_count", dict(n=len(first), items=first, text="%d lines with no earlier point (first count): %s" % (len(first), ", ".join(first[:12]) + (" …" if len(first) > 12 else ""))), who)
            con.commit()
        return n
    except Exception:                                         # noqa: BLE001
        try:
            con.rollback()
        except Exception:                                     # noqa: BLE001
            pass
        return 0


# ------------------------------------------------------------------ 3.6 leakage and the watch list
def count_periods(con, sp=None):
    """S430 (2.5): every closed count with a frozen run, as a PERIOD -- from the previous closed count's day (by day; the
    opening, 01-04-2026, before the first) to the count's day: its write-off (allowance + small + big at cost) and the
    period's sales (spine bills). One line per period; spread pro rata by month only for the cadence and the red rule."""
    ensure(con)
    sp = sp or Spine()
    out = []
    try:
        closed = sorted({dmy_to_iso(r[0]) for r in con.execute("SELECT c.marg_as_on FROM stock_count c JOIN stock_count_close k ON k.count_id=c.id WHERE c.id NOT IN (SELECT count_id FROM stock_count_part)")})
        runs = {}
        for r in con.execute("SELECT r.count_id, r.groups, c.marg_as_on FROM stock_writeoff_run r JOIN stock_count c ON c.id=r.count_id ORDER BY r.id"):
            try:
                g = json.loads(r[1])
            except ValueError:
                continue
            loss = sum((x.get("cost_p") or x.get("mrp_p") or 0) for k in ("allowance", "small", "big") for x in g.get(k, []))
            as_iso = dmy_to_iso(r[2])
            runs.setdefault(as_iso, 0)
            runs[as_iso] += loss
        for as_iso, loss_p in sorted(runs.items()):
            prevs = [d for d in closed if d < as_iso]
            frm = max(prevs) if prevs else OPENING_DAY
            sales_p = 0
            if sp.ok:
                r = sp.q("SELECT COALESCE(SUM(net_p),0) AS p FROM sp_sale_bill WHERE date>? AND date<=?", frm, as_iso)
                sales_p = int(r[0]["p"] or 0) if r else 0
            pct = (100.0 * loss_p / sales_p) if sales_p else None
            out.append(dict(frm=frm, to=as_iso, loss_p=loss_p, sales_p=sales_p, pct=(round(pct, 2) if pct is not None else None),
                            label="%s → %s" % (dt.date.fromisoformat(frm).strftime("%d-%b"), dt.date.fromisoformat(as_iso).strftime("%d-%b"))))
    except Exception:                                         # noqa: BLE001
        return []
    return out


def month_leak(con, ym, S=None, sp=None):
    """Leakage of a month (S430 dating): the month's loss points (spot counts, Darpan -- gap < 0, at cost) plus each count
    period's write-off spread pro rata by the month's share of the period's sales; the period itself is the line shown in
    the month the count closed ('01-Apr → 06-Sep: leakage ₹X = Y% of sales · budget 1%'). None when nothing can be read."""
    S = S or settings(con)
    sp = sp or Spine()
    ensure(con)
    points_p = 0
    try:
        # the count's own points (source full_count) are the period's write-off, dated by period -- never the month's spot losses too
        for r in con.execute("SELECT id, item, gap_units, at FROM stock_point WHERE substr(at,1,7)=? AND gap_units<0 AND source<>'full_count' AND status NOT IN ('superseded','recount','recounted')", (ym,)):   # S502; S936
            cost = None
            try:
                cost = _sa()._value_p(con, r[1], int(round(float(r[2]))))
            except Exception:                                 # noqa: BLE001 -- no rate on record: the spine's MRP stands in
                cost = None
            if cost:
                points_p += abs(int(cost))
            else:
                mrp = sp.mrp_p(r[1]) if sp.ok else None
                info = item_info(con, sp, r[1])
                points_p += int(round((mrp or 0) / max(1, info["pack"]) * abs(float(r[2])))) if mrp else 0
    except Exception:                                         # noqa: BLE001
        return None
    sales_p = sp.sales_month(ym) if sp.ok else 0
    m0 = ym + "-01"
    y, m = int(ym[:4]), int(ym[5:7])
    m1 = ("%04d-%02d-01" % (y + (1 if m == 12 else 0), 1 if m == 12 else m + 1))
    share_p, ends_here = 0, None
    for P in count_periods(con, sp):
        lo, hi = max(P["frm"], m0), min(P["to"], m1)          # the period's days inside this month: (lo, hi]
        if lo >= hi and not (P["frm"] < m1 and P["to"] >= m0):
            continue
        if P["to"][:7] == ym:
            ends_here = P
        if P["sales_p"] and sp.ok:
            r = sp.q("SELECT COALESCE(SUM(net_p),0) AS p FROM sp_sale_bill WHERE date>? AND date<=? AND date>=? AND date<?", P["frm"], P["to"], m0, m1)
            ms = int(r[0]["p"] or 0) if r else 0
            share_p += int(round(P["loss_p"] * ms / float(P["sales_p"])))
    loss_p = points_p + share_p
    if not sales_p:
        return dict(ym=ym, loss_p=loss_p, points_p=points_p, share_p=share_p, sales_p=0, pct=None, red=False, budget_pct=S["budget_pct"], period=ends_here,
                    text="Leakage %s -- no sales on record for the month" % rs(loss_p))
    pct = 100.0 * loss_p / sales_p
    red = pct > S["budget_pct"]
    if ends_here:
        text = "%s: leakage %s = %s of sales · budget %g%%" % (ends_here["label"], rs(ends_here["loss_p"]), ("%.1f%%" % ends_here["pct"]) if ends_here["pct"] is not None else "-", S["budget_pct"])
        if points_p:
            text += " · this month's spot counts %s" % rs(points_p)
    else:
        text = "Leakage %s = %.1f%% of sales · budget %g%%" % (rs(loss_p), pct, S["budget_pct"])
    return dict(ym=ym, loss_p=loss_p, points_p=points_p, share_p=share_p, sales_p=sales_p, pct=round(pct, 2), red=red, budget_pct=S["budget_pct"],
                period=ends_here, text=text, cls=("red" if red else "green"))


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

    def ortho(name):                                           # S430 (2.6): the orthotic section has its own cycle -- never on this list
        try:
            sa = _sa()
            return sa._item_section(con, dict(item=name)) == "Orthotics" or bool(sa._is_orthotic(name))
        except Exception:                                     # noqa: BLE001
            return False
    # first the items that earned the watch: two unexplained traces within a month; short at the last two closed counts
    for r in con.execute("SELECT DISTINCT ref FROM stock_watch_notice WHERE kind='close_watch' AND until>=?", (t.isoformat(),)):
        it = con.execute("SELECT item FROM stock_trace WHERE item_norm=? ORDER BY id DESC LIMIT 1", (r[0],)).fetchone()
        if it and r[0] not in names and not ortho(it[0]):
            picked.append((it[0], "two unexplained traces within a month", 0)); names.add(r[0])
    closed = [r[0] for r in con.execute("SELECT c.id FROM stock_count c JOIN stock_count_close k ON k.count_id=c.id WHERE c.id NOT IN (SELECT count_id FROM stock_count_part) ORDER BY c.id DESC LIMIT 2")]
    if len(closed) >= 2:
        a = {r[0] for r in con.execute("SELECT item FROM stock_diff WHERE count_id=? AND diff<0", (closed[0],))}
        b = {r[0] for r in con.execute("SELECT item FROM stock_diff WHERE count_id=? AND diff<0", (closed[1],))}
        for nm2 in sorted(a & b):
            if norm_name(nm2) not in names and not ortho(nm2):
                picked.append((nm2, "short at the last two counts", 0)); names.add(norm_name(nm2))
    # then the top items by sales value (never an orthotic), then the costly ones that sell -- or are dear enough to watch unsold
    rows = sp.q("SELECT k20, COALESCE(SUM((CASE WHEN UPPER(COALESCE(bill,'')) LIKE 'CN%' THEN -1 ELSE 1 END)*rate_p*units/NULLIF(CASE WHEN pack LIKE '1*%' THEN CAST(substr(pack,3) AS REAL) ELSE 1 END,0)),0) AS v, "
                "COALESCE(SUM(CASE WHEN UPPER(COALESCE(bill,'')) LIKE 'CN%' THEN -units ELSE units END),0) AS u "              # S454 P3B (18.5): a credit note is a return
                "FROM sp_sale_line WHERE date>=? GROUP BY k20 ORDER BY v DESC LIMIT ?", d90, S["watch_size"] + 40)
    sold90 = {r["k20"]: float(r["u"] or 0) for r in rows}
    n_top = 0
    for r in rows:
        if n_top >= S["watch_size"]:
            break
        it = sp.q("SELECT name FROM sp_item WHERE k20=? ORDER BY last_seen DESC LIMIT 1", r["k20"])
        if it and norm_name(it[0]["name"]) not in names and not ortho(it[0]["name"]):
            picked.append((it[0]["name"], "top by sales value", int(r["v"] or 0))); names.add(norm_name(it[0]["name"])); n_top += 1
    left_out = []
    for it in sp.items():
        if len(picked) >= S["watch_size"] + 20:
            break
        m = sp.mrp_p(it["name"])
        if not (m and m >= S["high_value_p"]) or norm_name(it["name"]) in names:
            continue
        if ortho(it["name"]):
            left_out.append((it["name"], "orthotic section")); continue
        if not sold90.get(it["k20"]) and m < S["dead_high_value_p"]:
            left_out.append((it["name"], "no sale in 90 days, under %s" % rs(S["dead_high_value_p"]))); continue
        why = "costly (%s a %s)" % (rs(m), "strip" if pack_of(it["packing"]) > 1 else "pc")
        if not sold90.get(it["k20"]):
            why += " -- no sale in 90 days, kept for its value"
        picked.append((it["name"], why, 0)); names.add(norm_name(it["name"]))
    out = []
    for name, why, v in picked:
        info = item_info(con, sp, name)
        pts = [dict(at=p[0], at_text=dmy(p[0][:10]), qty=p[1], gap=p[2], source=p[3], qty_text=qw(p[1], info["pack"], info["packing"], name),
                    gap_text=("" if p[2] is None else ("%s %s" % (qw(abs(p[2]), info["pack"], info["packing"], name), "short" if p[2] < 0 else ("over" if p[2] > 0 else "= records")))))
               for p in con.execute("SELECT at, qty_units, gap_units, source FROM stock_point WHERE item_norm=? AND status NOT IN ('superseded','recount','recounted') ORDER BY at DESC LIMIT 3", (norm_name(name),))]   # S502
        trend = []
        for i in range(2, -1, -1):
            m0 = (t.replace(day=1) - dt.timedelta(days=30 * i)).replace(day=1)
            m1 = (m0 + dt.timedelta(days=32)).replace(day=1)
            s = sp.sales(name, m0.isoformat(), (m1 - dt.timedelta(days=1)).isoformat(), incl_from=True)
            g = con.execute("SELECT COALESCE(SUM(CASE WHEN gap_units<0 THEN -gap_units ELSE 0 END),0) FROM stock_point WHERE item_norm=? AND at>=? AND at<? AND status NOT IN ('superseded','recount','recounted')", (norm_name(name), m0.isoformat(), m1.isoformat())).fetchone()[0]   # S502
            trend.append(dict(ym=m0.strftime("%Y-%m"), label=m0.strftime("%b"), sold=qw(s["u"], info["pack"], info["packing"], name), lost=(qw(g, info["pack"], info["packing"], name) if g else "")))
        out.append(dict(item=name, why=why, value_p=v, pack=info["pack"], packing=info["packing"], points=pts, trend=trend, mrp_p=sp.mrp_p(name)))
    LAST_LEFT_OUT[:] = left_out
    return out[:S["watch_size"] + 20]


LAST_LEFT_OUT = []                                             # S430: what the last watch_list() left out, and why (the report, the owner's card)


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
        spot_seen = False                                      # S494 (F-771): one spot-count line -- the newest (notices: newest first)
        for n in notices(con, "owner"):
            if n["kind"] in ("cadence", "plan_lapsed", "trace_unexplained", "spot_missed", "close_watch", "ortho_closed", "asked_count", "count_day", "s952_check") and n["at"][:10] >= (today() - dt.timedelta(days=7)).isoformat():   # S952: the daily self-check
                if n["kind"] == "spot_missed":
                    if spot_seen:
                        continue
                    spot_seen = True
                out.append(dict(cls=_s928_cls(n), target="stock", text=n["text"],
                                href=("/finance/stockcheck/" if n["kind"] in ("count_day", "asked_count", "s952_check") else None)))   # S436: ortho_closed; S894: asked_count; S928: count_day; S930: a count line opens the Stock check page
        out.extend(leak_needs_you(con, S, sp))
        out.extend(arrival_needs_you(con, sp))                  # S583
        out.extend(start_capture_lines(con, sp))                # S587 (D740)
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
        _s934_settle(con, sp)                                  # S934: a Count now judged to its bill once its day's sales are in
        R = build_roster(con, today(), S, sp)
        P = plan_state(con, S)
        p = P.get("plan")
        q = None
        if p and p["status"] == "picked":
            q = dict(id=p["id"], sunday=p["sunday"], sunday_text=p["sunday_text"], text_hi="Amir ne poori ginti ke liye Sunday %s chuna hai. Theek hai?" % p["sunday_text"])
        elif p and p["status"] == "confirmed":
            q = dict(id=p["id"], sunday=p["sunday"], sunday_text=p["sunday_text"], text_hi="Poori ginti: Sunday %s -- aapne haan kaha." % p["sunday_text"], confirmed=True)
        # S502 (D699, F-814): the last 7 days' lines that the system still believes (a voided line shows nowhere), in plain words
        losses = [dict(id=r[0], at=r[1], at_text=dmy(r[1][:10]), item=r[2],
                       text_hi="%s: %s — %s kam. Doctor sahab dekh rahe hain." % ("Aaj" if r[1][:10] == today().isoformat() else dmy(r[1][:10]), r[2], qw(r[3], int(r[4] or 1), r[5] or "", r[2], "hi")),
                       text="%s: %s %s short" % (dmy(r[1][:10]), r[2], qw(r[3], int(r[4] or 1), r[5] or "", r[2])))
                  for r in con.execute("SELECT id, at, item, gap_units, pack, packing FROM stock_watch_loss_line WHERE void_at IS NULL AND at >= ? ORDER BY id DESC LIMIT 12",
                                       ((today() - dt.timedelta(days=7)).isoformat(),))]
        tr = [t for t in traces(con, 12) if t["trigger"] in ("darpan", "point") and t["status"] == "open"]
        return dict(ok=True, roster=R, plan=q, losses=losses, traces=[dict(id=t["id"], item=t["item"], gap_hi=t["gap_hi"], verdict_hi=t["verdict_hi"], entry_error=t["entry_error"],
                                                                        text_hi=("Aapki baat sahi thi -- entry ki galti thi (%s)" % t["fix"]) if t["entry_error"] else ("%s: %s -- %s" % (t["item"], t["gap_hi"], t["verdict_hi"]))) for t in tr],
                    notices=notices(con, "darpan"), is_spot_day=R["is_spot_day"], now=now_view(con, sp, who))   # S934: Abhi ginti
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
        nxt = next_roster_day(S, t, con)
        ym = t.strftime("%Y-%m")
        approx_lines = ["%s: counted %s against a family figure (approximate) \u2014 not judged" % (r[0], qw(r[1], int(r[2] or 1), r[3] or "", r[0]))
                        for r in con.execute("SELECT p.item, p.qty_units, COALESCE(s.pack,1), COALESCE(s.packing,'') FROM stock_point p LEFT JOIN stock_spot_roster s ON s.point_id=p.id "
                                             "WHERE p.basis='approx' AND p.status<>'superseded' AND p.at>=? ORDER BY p.id DESC LIMIT 12", ((t - dt.timedelta(days=30)).isoformat(),))]   # S577
        return dict(ok=True, plan=P, roster_today=R, next_day=(nxt.isoformat() if nxt else None), next_day_text=(dmy(nxt.isoformat()) if nxt else ""),
                    roster_next=(preview_roster(con, nxt, S, sp) if nxt else []), watch=watch_list(con, S, sp, root), watch_left_out=list(LAST_LEFT_OUT), approx_lines=approx_lines,
                    traces=[x for x in traces(con, 80) if x["verdict"] != "first_count"][:20],     # S430: the count's own lines collapse to one line
                    first_count_n=con.execute("SELECT COUNT(*) FROM stock_trace WHERE verdict='first_count'").fetchone()[0],
                    first_count_items=[r[0] for r in con.execute("SELECT item FROM stock_trace WHERE verdict='first_count' ORDER BY item")],
                    tap_vs_bill=tap_vs_bill_lines(con), leak=month_leak(con, ym, S, sp), leak_prev=month_leak(con, (t.replace(day=1) - dt.timedelta(days=1)).strftime("%Y-%m"), S, sp),
                    settings=settings_view(con), notices=notices(con, "owner"),
                    asks=[dict(id=r[0], item=r[1], by=r[2], at_text=stamp(r[3])) for r in con.execute("SELECT id, item, by, at FROM stock_watch_ask WHERE done_at IS NULL ORDER BY id")],
                    points_n=con.execute("SELECT COUNT(*) FROM stock_point").fetchone()[0], spot_days=S["spot_days"], cap=S["cap"])
    except Exception as e:                                    # noqa: BLE001
        return dict(ok=False, note=str(e)[:160])


def cached_big_lines(con, root):
    """S432: the Big-loss lines as the desk's cache holds them (loss_piles.stock_pile_cache) -- for the traces, without a report."""
    try:
        return [json.loads(r[0]) for r in con.execute("SELECT line_json FROM stock_pile_cache WHERE count_id=? AND bucket='bigloss'", (int(root),))]
    except sqlite3.Error:
        return []


def refresh_owner_view(con, root, who="system", lines=None, sp=None):
    """S432: THE ONE PLACE the watch is scored -- the traces on the Big-loss lines given (or the cached ones), then owner_view(),
    stored with its time. The 06:30 job, 'Refresh watch' and the very first read call this; a plain read never does."""
    ensure(con)
    t0 = dt.datetime.now()
    sp = sp or Spine()
    n_tr = 0
    try:
        ls = lines if lines is not None else cached_big_lines(con, root)
        if ls:
            n_tr = trace_big_losses(con, root, ls, who, sp=sp)
    except Exception:                                         # noqa: BLE001
        n_tr = 0
    V = owner_view(con, root)
    ts = now_iso()
    ms = int((dt.datetime.now() - t0).total_seconds() * 1000)
    V.update(stored_at=ts, stored_text=stamp(ts), refreshed_by=who, refresh_ms=ms, traces_opened=n_tr, stored=True)   # S436: stamp() already says IST
    try:
        con.execute("INSERT OR REPLACE INTO stock_watch_view (key, root, made_at, made_by, ms, traces_n, json) VALUES ('owner',?,?,?,?,?,?)",
                    (int(root or 0), ts, who, ms, n_tr, json.dumps(V, default=str, separators=(",", ":"))))
        _audit(con, "watch_refresh", dict(root=int(root or 0), ms=ms, traces=n_tr, text="watch refreshed by %s in %d ms (%d trace%s opened)" % (who, ms, n_tr, "" if n_tr == 1 else "s")), who)
        con.commit()
    except sqlite3.Error:
        pass
    return V


def stored_owner_view(con, root, build_if_missing=True):
    """S432: the watch card as last stored, with its time -- what the desk read shows. Nothing stored yet -> built once."""
    ensure(con)
    try:
        r = con.execute("SELECT made_at, made_by, ms, json FROM stock_watch_view WHERE key='owner'").fetchone()
    except sqlite3.Error:
        r = None
    if r:
        try:
            V = json.loads(r[3])
            V.update(stored_at=r[0], stored_text=stamp(r[0]), refreshed_by=r[1] or "", stored=True)   # S436: stamp() already says IST
            return V
        except ValueError:
            pass
    if not build_if_missing:
        return dict(ok=False, note="not refreshed yet", stored=False)
    return refresh_owner_view(con, root, "first read", lines=[])   # the very first build scores the watch; it opens no trace (the close / Refresh do)


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



# ------------------------------------------------------------------ S934 (23-Nov-2026): COUNT NOW, placed to the bill
#  THE OWNER'S WORD (23-Nov 08:16-08:22): his Count button offers 'Count now' or 'Next list'. A Count now reaches Darpan's screen at once
#  ('Abhi ginti', above the morning list) and Darpan keys the LAST SALE BILL number with his count, so the count is placed to the bill:
#  the sales billed up to that number left the shelf before he counted, the rest after. Such a point is saved at once and JUDGED when the
#  day's sale report is in (status 'awaits_sales'): expected = the figure at the END of the count day (the shelf figure for a counted
#  item, Marg's for an uncounted one; the point itself left out) + that day's sales billed AFTER the number. Carried forward
#  (stock_figure.shelf) the count day's sales up to the number are not taken off again. No number keyed -> the time rule, as any spot
#  count. A Next-list ask is the morning roster's, as before. His open asks can be withdrawn (a rostered row not yet counted leaves that
#  day's list). The installer withdraws every ask open at the install (his word 08:22: "clear whatever counts I have raised").
S934_BILL_SPAN = 300                                          # a number further than this past the last known bill is refused as a typo


def _s934_columns(con):
    """S934: stock_watch_ask.mode ('now' | 'next'; NULL = 'next') and .closed_how ('counted' | 'withdrawn'); stock_point.last_bill (the
    sale bill number a Count now was placed to) and .ask_id. Additive."""
    for t, c, ty in (("stock_watch_ask", "mode", "TEXT"), ("stock_watch_ask", "closed_how", "TEXT"),
                     ("stock_point", "last_bill", "TEXT"), ("stock_point", "ask_id", "INTEGER")):
        try:
            cols = {r[1] for r in con.execute("PRAGMA table_info(%s)" % t).fetchall()}
            if cols and c not in cols:
                con.execute("ALTER TABLE %s ADD COLUMN %s %s" % (t, c, ty))
        except sqlite3.Error:
            pass


def _s934_bill_no(text):
    """'4951' / 'A004951' / 'a 4951' -> 4951; None when there is no number (or more than 7 digits)."""
    d = "".join(re.findall(r"\d+", str(text or "")))
    if not d or len(d.lstrip("0") or "0") > 7:
        return None
    return int(d)


def _s934_last_known(con, day=None):
    """(day, last sale bill number) of the newest day BEFORE `day` (today) in Marg's bill chain, series A; (None, None) when unread."""
    d = day or today().isoformat()
    try:
        r = con.execute("SELECT day, last_no FROM mi_bill_chain WHERE series='A' AND last_no IS NOT NULL AND day<? ORDER BY day DESC LIMIT 1", (d,)).fetchone()
        return (r[0], int(r[1])) if r else (None, None)
    except sqlite3.Error:
        return (None, None)


def _s934_check_bill(con, text, day=None):
    """(ok, number, Hindi message). Refused: no number; a number BEFORE the last bill of the last day known (yesterday's report); a
    number more than S934_BILL_SPAN past it (a typo). Unknown chain -> accepted."""
    n = _s934_bill_no(text)
    if n is None or n <= 0:
        return False, None, "Aakhri bill ka number likhiye (jaise 4951)."
    ld, last = _s934_last_known(con, day)
    if last is not None:
        t_ = today()
        if n < last and t_.month == 4 and t_.day <= 7 and n < 1000:   # a new financial year: Marg's A series starts again
            return True, n, ""
        if n < last:
            return False, None, "Yeh number %s ke aakhri bill (%d) se peechhe hai. Aaj ka aakhri bill number dobara dekhiye." % (dmy(ld), last)
        if n > last + S934_BILL_SPAN:
            return False, None, "Yeh number bahut aage hai (%s ka aakhri bill %d tha). Dobara dekhiye." % (dmy(ld), last)
    return True, n, ""


def _s934_unroster(con, item, who, ask_id, ask_at):
    """Every roster row of THIS ask for the item that Darpan has not answered -- the row it was put on AND any copy carried onto a later
    list (a carried row is a new row the ask's roster_id never points to): reason 'you asked for it...', on or after the ask's own day (an
    older ask's rows are history). A system pick is never touched."""
    rows = con.execute("SELECT id, day FROM stock_spot_roster WHERE item_norm=? AND answered_at IS NULL AND reason LIKE 'you asked for it%' AND day>=?",
                       (norm_name(item), str(ask_at or "")[:10])).fetchall()
    for rid, day in rows:
        con.execute("DELETE FROM stock_spot_roster WHERE id=?", (rid,))
        _audit(con, "roster_row_withdrawn", dict(roster_id=rid, day=day, item=item, ask_id=ask_id), who, rid)
    return len(rows)


def withdraw_ask(con, ask_id, who):
    """The owner withdraws an open ask (S934). A rostered row Darpan has not answered leaves that day's list; nothing is deleted from a
    count. Returns (ok, message, code)."""
    ensure(con)
    try:
        aid = int(ask_id)
    except (TypeError, ValueError):
        return False, "Which ask?", 400
    r = con.execute("SELECT id, item, roster_id, at FROM stock_watch_ask WHERE id=? AND done_at IS NULL", (aid,)).fetchone()
    if not r:
        return False, "That ask is no longer open.", 404
    rof = con.execute("SELECT recount_of FROM stock_watch_ask WHERE id=?", (aid,)).fetchone()
    if rof and rof[0] is not None:                             # S936 (review 2, finding 6): the held count would stay held for good
        return False, "%s is a recount the system asked for -- Darpan's next count of it settles it." % r[1], 409
    _s934_unroster(con, r[1], who, r[0], r[3])
    con.execute("UPDATE stock_watch_ask SET done_at=?, closed_how='withdrawn' WHERE id=?", (now_iso(), r[0]))
    _audit(con, "ask_withdrawn", dict(ask_id=r[0], item=r[1]), who, r[0])
    con.commit()
    return True, "%s withdrawn -- off Darpan's list." % r[1], 200


def withdraw_all_open(con, who):
    """The installer's one-off (his word 08:22): every ask open now, withdrawn. Returns the items."""
    ensure(con)
    out = []
    for (aid,) in con.execute("SELECT id FROM stock_watch_ask WHERE done_at IS NULL ORDER BY id").fetchall():
        ok, msg, _c = withdraw_ask(con, aid, who)
        if ok:
            out.append(msg.split(" withdrawn")[0])
    return out


def now_view(con, sp=None, who=None):
    """Darpan's 'Abhi ginti' card: the open Count-now asks, oldest first, with the last bill known (a hint, never a default). S936: a recount
    ask carries its question (recount, why_hi); sitting_bill = the bill this person keyed in this sitting (D1047), carried to every item."""
    try:
        ensure(con)
        sp = sp or Spine()
        items = []
        for aid, item, at, rof, why_hi in con.execute("SELECT id, item, at, recount_of, why_hi FROM stock_watch_ask WHERE done_at IS NULL AND mode='now' ORDER BY id").fetchall():
            info = item_info(con, sp, item)
            pack, packing = int(info.get("pack") or 1), info.get("packing") or ""
            name = info.get("item") or item
            items.append(dict(id=aid, item=name, pack=pack, packing=packing, whole_hi=_qwm().whole_word(packing, None, name, pack, "hi"),
                              at=at, at_text=stamp(at), recount=bool(rof), why_hi=(why_hi or "")))
        ld, last = _s934_last_known(con)
        S = settings(con)
        sb, age = _s936_sitting(con, who)
        return dict(items=items, last_day=(dmy(ld) if ld else ""), last_no=last, sitting_bill=sb, sitting_age_s=age, sitting_minutes=int(S["sitting_minutes"]))
    except Exception:                                         # noqa: BLE001
        return dict(items=[], last_day="", last_no=None, sitting_bill=None, sitting_age_s=None, sitting_minutes=60)


def answer_now(con, ask_id, qty_units, last_bill, who, sp=None, no_bill=False):
    """Darpan answers a Count now: the shelf quantity and the last sale bill number. With a number the point waits for that day's sale
    report ('awaits_sales') and is judged to the bill (_s934_settle); without one it is judged now by its time, as any spot count.
    Returns (ok, message_hi, code, point)."""
    ensure(con)
    sp = sp or Spine()
    try:
        aid = int(ask_id)
    except (TypeError, ValueError):
        aid = 0
    r = con.execute("SELECT id, item FROM stock_watch_ask WHERE id=? AND done_at IS NULL AND mode='now'", (aid,)).fetchone()
    if not r:
        return False, "Yeh ginti ab khuli nahi hai.", 404, None
    n = None
    sitting = False
    if not str(last_bill or "").strip() and not no_bill:      # S936 (D1047): an item saved without a bill in a sitting takes the sitting's bill
        sb = _s936_sitting_bill(con, who)
        if sb is not None:
            last_bill, sitting = str(sb), True
    if str(last_bill or "").strip():
        ok, n, msg = _s934_check_bill(con, last_bill)
        if not ok:
            return False, msg, 400, None
    if n is None:
        P = write_point(con, r[1], qty_units, "darpan", who, sp=sp, note="Count now (no bill number -- placed by its time)", commit=False)
    else:
        P = write_point(con, r[1], qty_units, "darpan", who, sp=sp, note="Count now, to bill %d" % n, expected=None, commit=False)
        con.execute("UPDATE stock_point SET status='awaits_sales', settled_at=NULL, last_bill=?, expected_units=NULL, gap_units=NULL WHERE id=?",
                    (str(n), P["id"]))
        P.update(status="awaits_sales", expected=None, gap=None, last_bill=n,
                 verdict="counted to bill %d -- judged when that day's sale report is in" % n,
                 verdict_hi="Bill %d tak ki ginti -- kal ki sale report aane par milaan hoga." % n)
    con.execute("UPDATE stock_point SET ask_id=? WHERE id=?", (r[0], P["id"]))
    con.execute("UPDATE stock_watch_ask SET done_at=?, closed_how='counted' WHERE id=?", (now_iso(), r[0]))
    _audit(con, "count_now", dict(ask_id=r[0], item=P["item"], qty=float(qty_units), last_bill=n, sitting=sitting), who, P["id"])
    _s936_open_recount(con, P, who)                            # S936: a count by its time held for a recount
    con.commit()
    _s928_count_day(con, sp)
    tail = (" (is baithak ka bill %d)" % n if sitting else "") if n is not None else " Bill number nahi likha -- samay se milaan hua."   # S936
    return True, ("Likh liya: %s -- %s. %s%s" % (P["item"], P["qty_hi"], P["verdict_hi"], tail)).rstrip(), 200, P


def _s934_sales_in(con, sp, day):
    """True only when the SPINE holds a sale report covering `day` to its end: an accepted SALE_BILLWISE export whose date_to is on or after
    the day and that was taken AFTER the day (its stamp's date later than the day). Marg's bill chain is never enough: it is rebuilt the
    moment the report lands, the spine minutes to hours later (cold review, MUST 1)."""
    try:
        for r in sp.q("SELECT stamp, date_to FROM sp_export WHERE family='SALE_BILLWISE' AND ok=1 AND date_to>=? AND COALESCE(date_from,'')<=?", day, day):   # second look A: the report must COVER the day
            st = str(r.get("stamp") or "")[:8]
            if len(st) == 8 and st.isdigit() and "%s-%s-%s" % (st[:4], st[4:6], st[6:8]) > day:
                return True
    except Exception:                                         # noqa: BLE001
        pass
    return False


def _s934_settle(con, sp=None):
    """Judge every 'awaits_sales' point whose day's sales are in: expected = the figure at the END of the count day (shelf for a counted
    item, Marg's for an uncounted one; the point itself left out) + that day's sales billed AFTER its last bill; a family figure is not
    judged. A short beyond the allowance is a loss line by name, as write_point. Fail-soft per point. Returns the number judged."""
    try:
        ensure(con)
        rows = con.execute("SELECT id, item, at, qty_units, last_bill FROM stock_point WHERE status='awaits_sales' ORDER BY at, id").fetchall()
    except sqlite3.Error:
        return 0
    if not rows:
        return 0
    sp = sp or Spine()
    if not getattr(sp, "ok", False):
        return 0
    SF = _sf()
    n, days = 0, set()
    for pid, item, at, q, lb in rows:
        D = str(at)[:10]
        try:
            if not _s934_sales_in(con, sp, D):
                continue
            ctx = SF.Ctx(con, sp)
            N = _s934_bill_no(lb)
            b0 = SF.base(con, item, ctx, exclude_id=pid)
            if b0 is not None and str(b0.get("at") or "") > str(at):      # SHOULD 3: a later count of the item already stands
                con.execute("UPDATE stock_point SET status='settled', settled_at=?, note=COALESCE(note,'') || ? WHERE id=?",
                            (now_iso(), " · a later count stands -- not judged", pid))
                _audit(con, "point_not_judged_later_count", dict(point_id=pid, item=item, later_at=b0.get("at")), "system", pid)
                con.commit()
                n += 1
                days.add(D)
                continue
            E952 = _s952_judge(con, sp, item, at, q, last_bill=lb, exclude_id=pid, ctx=ctx)   # S952 (D1065): the one record, to the bill
            if E952 is not None and E952.get("awaits"):
                continue
            Sh = SF.shelf(con, sp, item, D, ctx, exclude_id=pid)
            M = SF.marg(con, sp, item, D, ctx)
            k = Sh.get("key") or SF.key_of(sp, item, ctx)
            after = float(SF.day_sales_cut(sp, k, D, N, after=True)) if (k and N is not None) else 0.0
            late = float(SF.taps(con, sp, item, at, ctx) or 0) + float(SF.scan_arrivals(con, sp, item, at, ctx) or 0)   # MUST 2: arrivals AFTER the count
            pr_d = (sp.q("SELECT COUNT(*) AS n FROM sp_move WHERE k20=? AND date=? AND kind='PURCHASE'", k, D) or [{"n": 0}])[0]["n"] if k else 0
            if Sh.get("approx") or (M and M.get("approx")):
                basis, exp = "approx", None
            elif Sh.get("shelf") is not None:
                basis, exp = "shelf", float(Sh["shelf"]) + after - late
            elif M is not None:
                sa = float(SF.scan_arrivals(con, sp, item, M["closing"]["stamp_iso"], ctx) or 0)   # SHOULD 5: as expect_for_point
                basis, exp = "marg", float(M["figure"]) + float(M.get("taps") or 0) + sa + after - late
            else:
                basis, exp = "marg", None
            if E952 is not None:                              # S952: the record's judgment replaces the shelf / Marg branch above
                basis, exp = E952.get("basis"), E952.get("expected")
                pr_d = bool(E952.get("never_loss")) and not E952.get("near_delivery")   # about a delivery: the recount rule (S936) still asks
                if E952.get("words"):
                    _s952_words(con, pid, E952["words"])
            gap = None if exp is None else round(float(q) - exp, 3)
            note_add = " · a purchase is dated that day (its time is not known) -- the gap is shown, never a loss" if (pr_d and E952 is None) else ""
            con.execute("UPDATE stock_point SET expected_units=?, gap_units=?, status='settled', settled_at=?, basis=?, note=COALESCE(note,'') || ? WHERE id=?",
                        (exp, gap, now_iso(), basis, note_add, pid))
            if gap is not None and gap < 0 and basis != "approx" and not pr_d:
                info = item_info(con, sp, item)
                pr = con.execute("SELECT at FROM stock_point WHERE item_norm=? AND id<>? AND at<? AND COALESCE(status,'')<>'superseded' ORDER BY at DESC LIMIT 1",
                                 (norm_name(item), pid, at)).fetchone()
                since = str(pr[0])[:10] if pr else (dt.date.fromisoformat(D) - dt.timedelta(days=30)).isoformat()
                allow, _sold = allowance_units(con, item, info["pack"], since, sp)
                if E952 is not None and E952.get("allowance") is not None:   # S952: the judgment's own allowance
                    allow = E952["allowance"]
                H = None if _s936_is_recount_point(con, pid) else _s936_match(con, sp, item, at, -gap, info["pack"], pid)   # S936 (D1046)
                if abs(gap) > allow and H is not None:       # a bill-placed count short by about a fresh delivery: HELD, a recount by itself
                    _s936_hold_row(con, pid, H, (con.execute("SELECT note FROM stock_point WHERE id=?", (pid,)).fetchone() or [None])[0])
                    _s936_open_recount(con, dict(id=pid, item=item, status="recount", hold=H), "system")
                elif abs(gap) > allow and not (E952 is not None and E952.get("near_delivery")):   # S952: a delivery's worth short is never booked
                    mrp = sp.mrp_p(item) if sp.ok else None
                    per = (mrp / max(1, info["pack"])) if mrp else None
                    con.execute("INSERT INTO stock_watch_loss_line (at, item, gap_units, pack, packing, mrp_p, point_id) VALUES (?,?,?,?,?,?,?)",
                                (at, item, abs(gap), info["pack"], info["packing"], (int(round(per * abs(gap))) if per else None), pid))
                    try:
                        open_trace(con, item, "point", gap, "system", sp=sp, point_id=pid)
                    except Exception:                         # noqa: BLE001
                        pass
            _audit(con, "point_judged_to_bill", dict(point_id=pid, item=item, day=D, last_bill=N, sold_after=after, arrived_after=late, purchase_that_day=bool(pr_d),
                                                     expected=exp, gap=gap, basis=basis), "system", pid)
            con.commit()
            n += 1
            days.add(D)
        except Exception:                                     # noqa: BLE001
            try:
                con.rollback()
            except Exception:                                 # noqa: BLE001
                pass
    for D in sorted(days):
        _s928_count_day(con, sp, D)
    return n


def _s952_judge(con, sp, item, at, qty, last_bill=None, exclude_id=None, ctx=None, live=False):
    """S952 (D1065): record_judges.expect -- the count against THE ONE RECORD (Marg's figure at its moment + the deliveries truly on the
    shelf and not in Marg; an older loss not yet written off never booked twice) -- or None (the switch count.judge_by_record off, or a
    failure: the caller's own path, as before)."""
    try:
        import record_judges                                  # noqa: PLC0415 -- beside this file
        return record_judges.expect(con, sp, item, at, qty, last_bill, exclude_id, ctx, live)
    except Exception as ex:                                   # noqa: BLE001 -- a count is never refused for it
        print("stock_watch: the S952 judgment failed for %s (%s) -- the old figure is used" % (item, ex), file=sys.stderr)
        return None


def _s952_words(con, pid, words):
    """The judgment's words on the point (stock_point.judge_words, added by record_judges.ensure). Fail-soft."""
    try:
        con.execute("UPDATE stock_point SET judge_words=? WHERE id=?", (str(words)[:600], int(pid)))
    except sqlite3.Error:
        pass


# ------------------------------------------------------------------ the job (cron 06:30 IST)
def job(db_path, who="cron"):
    con = sqlite3.connect(db_path, timeout=60)
    ensure(con)
    S = settings(con)
    sp = Spine()
    settle_provisional(con, sp)
    R = build_roster(con, today(), S, sp, who=who, asks_ok=True)   # S958: the morning job writes his asks-only morning
    P = plan_state(con, S, who=who)
    auto_adjust(con, S, who=who)
    n_bill = len(bill_pending_lines(con, S, sp))
    # S432: the watch scored and stored here, once a day (and on 'Refresh watch'), never on the desk's read
    try:
        root = con.execute("SELECT MAX(id) FROM stock_count WHERE id NOT IN (SELECT count_id FROM stock_count_part)").fetchone()[0] or 0
        V = refresh_owner_view(con, root, who, sp=sp)
        wtxt = "watch stored for count #%d in %d ms (%d trace%s opened)" % (root, V.get("refresh_ms") or 0, V.get("traces_opened") or 0, "" if V.get("traces_opened") == 1 else "s")
    except Exception as e:                                    # noqa: BLE001
        wtxt = "watch NOT stored: %s" % str(e)[:120]
    print("%s stock_watch job: %s%s roster %d item(s) [%s]; plan %s; bill-entry pending %d; %s" % (
        now_iso(), R["day"], "" if R["is_spot_day"] else " (not a spot day)", len(R["items"]), ", ".join(x["item"] for x in R["items"]),
        (P["plan"]["status"] if P.get("plan") else "none due (from %s)" % P["due_from"]), n_bill, wtxt))
    con.close()
    return 0



# ==========================================================================================================================================
# S454_BILL_REGISTER part 3 (03-Oct-2026, S454 9.2 / 9.3, D667): a spot-count answer is compared with the SHELF FIGURE (shelf_figure: the newest
# count carried forward by the spine's sales and purchases, plus what arrived and is not yet in Marg) -- the records' expectation from Marg's
# latest closing stays the fallback (an item no count has reached, or no spine). An item flagged at the newest closing (the shelf figure and
# Marg moved apart with no voucher) is one more reason in the roster's ranking, never past its cap.
# ==========================================================================================================================================
def _s454_expected(con, sp, item):
    """S577: stock_figure.expect_for_point -- basis 'shelf' (a counted item: the shelf figure), 'marg' (uncounted: Marg's figure by the
    one capture rule, plus taps) or 'approx' (a size that shares a family figure: no figure, no verdict). Fail-soft: no figure at all."""
    try:
        return _sf().expect_for_point(con, sp, item)
    except Exception:                                         # noqa: BLE001 -- the count is never refused for it
        return dict(expected=None, provisional=0.0, as_on=None, close=None, sold=0.0, bought=0.0, basis=None, records=None, terms=[])


def _s454_gap_flag(con, nm, ctx=None):
    try:
        import shelf_figure                                   # noqa: PLC0415
        return shelf_figure.gap_flag(con, nm, ctx)
    except Exception:                                         # noqa: BLE001
        return 0
# ---- S454 part 3 end -------------------------------------------------------------------------------------------------------------------


# ------------------------------------------------------------------ S936 (23-Nov-2026): THE RECOUNT RULE (D1046) and ONE BILL PER SITTING (D1047)
#  THE OWNER, 23-Nov 11:18 (TRAMATEE P: Saturday's 9:4 counted without Mannat's 40 strips became the shelf, booked a false loss line and put 50
#  strips on Monday's order list on "on hand 4:0"): "confusing ... might also spoil the purchase order generation". A count is evidence, not the
#  truth. A count short of the expected figure by ABOUT A FRESH DELIVERY (an arrival tapped or scan-tied, its scanned bill's quantity, or a Marg
#  purchase line, within count.recount_days before the count; the shortfall within count.recount_tol_pct of the delivery) is HELD: status
#  'recount' -- never the shelf base (stock_figure.points leaves it out, so the order engine, the stock of record and every judgment never see
#  it), no loss line, no trace, out of the month's leakage and the watch list; ONE Count-now ask is opened by itself (by 'system', recount_of =
#  the held point) with the question for Darpan. The next count of the item answers it: the held point becomes 'recounted' (any line or trace
#  of it voided) and the new count is judged as any count -- never held itself (a recount that is short again is a loss by name).
#  THE OWNER, 23-Nov 11:41: "one bill per sitting" -- Darpan counts many items at one bill. The card takes the bill once and carries it; the
#  server takes the sitting's bill (_s936_sitting_bill: his newest Count now with a bill today within count.sitting_minutes) when an item comes
#  with none and the page did not say 'no bill' (a page from before the kit, or a lost field).
RECOUNT_ST = ("recount", "recounted")


def _s936_columns(con):
    """S936: stock_watch_ask.recount_of (the held point a system recount asks about), .why (English), .why_hi (Darpan's question);
    stock_point.recount_for (the held point this count answered -- such a count, and any correction of it, is never held). Additive."""
    for t, c, ty in (("stock_watch_ask", "recount_of", "INTEGER"), ("stock_watch_ask", "why", "TEXT"), ("stock_watch_ask", "why_hi", "TEXT"),
                     ("stock_point", "recount_for", "INTEGER")):
        try:
            cols = {r[1] for r in con.execute("PRAGMA table_info(%s)" % t).fetchall()}
            if cols and c not in cols:
                con.execute("ALTER TABLE %s ADD COLUMN %s %s" % (t, c, ty))
        except sqlite3.Error:
            pass


def _s936_recount_for(con, pid):
    """The held point a count answered (stock_point.recount_for), or None."""
    try:
        r = con.execute("SELECT recount_for FROM stock_point WHERE id=?", (int(pid),)).fetchone()
        return int(r[0]) if (r and r[0] is not None) else None
    except sqlite3.Error:
        return None


def _s936_open_recount_ask(con, item):
    """(ask id, held point id) of the item's open recount, or None."""
    try:
        r = con.execute("SELECT id, recount_of FROM stock_watch_ask WHERE item_norm=? AND done_at IS NULL AND recount_of IS NOT NULL ORDER BY id LIMIT 1",
                        (norm_name(item),)).fetchone()
        return (int(r[0]), int(r[1])) if r else None
    except sqlite3.Error:
        return None


def _s936_hm(ts):
    s = str(ts or "")
    return ("%s-%s %s" % (s[8:10], s[5:7], s[11:16])) if len(s) >= 16 else dmy(s)


def _s936_close_recount(con, rc, pid, ts, who):
    """The count `pid` answers the open recount rc = (ask, held point): the ask closed as counted; the held point 'recounted' (its note names
    the new point); any loss line of it voided and any trace of it closed. Inside the caller's transaction (no commit)."""
    aid, held = rc
    con.execute("UPDATE stock_watch_ask SET done_at=?, closed_how='counted' WHERE id=? AND done_at IS NULL", (ts, aid))
    r0 = con.execute("SELECT item_norm FROM stock_point WHERE id=?", (int(pid),)).fetchone()
    if r0:                                                     # any other open RECOUNT of the item is answered too; his own asks close by their callers (his notice stays, review 2 finding 3)
        con.execute("UPDATE stock_watch_ask SET done_at=?, closed_how='counted' WHERE item_norm=? AND done_at IS NULL AND recount_of IS NOT NULL", (ts, r0[0]))
    con.execute("UPDATE stock_point SET recount_for=? WHERE id=?", (held, int(pid)))
    _s936_touch(con)
    r = con.execute("SELECT note FROM stock_point WHERE id=?", (held,)).fetchone()
    con.execute("UPDATE stock_point SET status='recounted', note=? WHERE id=? AND status IN ('recount','recounted')",
                ("recounted %s -- %s" % (_s936_hm(ts), str((r[0] if r else "") or "")), held))
    con.execute("UPDATE stock_watch_loss_line SET void_at=?, void_why='recounted' WHERE point_id=? AND void_at IS NULL", (ts, held))
    con.execute("UPDATE stock_trace SET status='fixed', seen_by='S936 recount', seen_at=? WHERE status<>'fixed' AND json_extract(findings_json,'$.point_id')=?",
                (ts, held))
    _audit(con, "recount_answered", dict(ask_id=aid, held_point=held, new_point=pid), who, pid)


def _s936_withdraw_for(con, held_pid, who):
    """A recount asked about a count that is being CORRECTED (correct_roster) is not the correction's to answer: withdrawn. No commit."""
    for (aid,) in con.execute("SELECT id FROM stock_watch_ask WHERE recount_of=? AND done_at IS NULL", (int(held_pid),)).fetchall():
        con.execute("UPDATE stock_watch_ask SET done_at=?, closed_how='withdrawn' WHERE id=?", (now_iso(), aid))
        _audit(con, "recount_withdrawn", dict(ask_id=aid, held_point=int(held_pid), why="the count was corrected"), who, aid)


def _s936_is_recount_point(con, pid):
    """True when the point answered a recount (stock_point.recount_for, or its ask_id is a system recount) -- such a count is never held."""
    if _s936_recount_for(con, pid) is not None:
        return True
    try:
        r = con.execute("SELECT a.recount_of FROM stock_point p JOIN stock_watch_ask a ON a.id=p.ask_id WHERE p.id=?", (int(pid),)).fetchone()
        return bool(r and r[0])
    except sqlite3.Error:
        return False


def _s936_match(con, sp, item, at_iso, short_units, pack=1, pid=None):
    """The fresh delivery a shortfall is about the size of, or None. Deliveries: the item's arrivals tapped from count.recount_days before the
    count -- and never before the base count the point is judged on (a delivery the last count already saw is no missed carton) -- up to its
    moment (the tapped quantity AND its bill's, when known), and Marg's purchase lines of the item dated in those days (the spine). 'About':
    |shortfall - delivery| within count.recount_tol_pct of the delivery (at least half a strip / pc of slack). The closest wins. A shortfall
    under one strip / pc is never a carton. Fail-soft: None."""
    try:
        short = float(short_units or 0)
        pk = max(1, int(pack or 1))
        if short < pk:
            return None
        S = settings(con)
        tol, days = float(S["recount_tol_pct"]) / 100.0, int(S["recount_days"])
        at = str(at_iso or now_iso())[:19]
        lo = (dt.datetime.fromisoformat(at) - dt.timedelta(days=days)).replace(microsecond=0).isoformat()
        base_day = None
        after_bills = set()
        try:                                                   # the review (S506, finding 7): the window starts no earlier than the base count
            SF = _sf()
            b = SF.base(con, item, SF.Ctx(con, sp), exclude_id=pid)
            if b is not None:
                base_day = str(b.get("day") or b.get("at") or "")[:10] or None
                if str(b.get("at") or "")[:19] > lo:
                    lo = str(b["at"])[:19]
                if hasattr(SF, "s956_after_bills"):            # S957 (the S956 review): a bill S956 adds after a morning count is not in that count
                    after_bills = SF.s956_after_bills(con, sp, item, b)
        except Exception:                                     # noqa: BLE001
            pass
        cands = []
        keys = {pad_norm(item[:27]), pad_norm(item)}
        try:
            rows = con.execute("SELECT l.item, l.supplied, l.pack_size, l.arrived_at, l.billed_qty, l.billed_bill_no, l.billed_date, o.vendor FROM purchase_order_line l "
                               "JOIN purchase_order o ON o.id=l.order_id WHERE l.arrived_at IS NOT NULL AND l.arrived_at>=? AND l.arrived_at<=? AND l.supplied>0",
                               (lo, at)).fetchall()
        except sqlite3.Error:
            rows = []
        for nm, supplied, ps, arrived, bq, bno, bdate, vendor in rows:
            if pad_norm(str(nm)[:27]) not in keys and pad_norm(nm) not in keys:
                continue
            ps_ = float(ps or 1)
            for u in sorted({float(supplied or 0) * ps_, float(bq or 0) * ps_}):
                if u > 0:
                    cands.append(dict(units=u, bill=str(bno or ""), vendor=str(vendor or ""), day=str(bdate or arrived or "")[:10]))
        if sp is not None and getattr(sp, "ok", False):
            for p in sp.purchases(item, lo[:10], at[:10], incl_from=True):
                if p.get("direction") == "RETURN":
                    continue
                if base_day and str(p.get("date") or "")[:10] <= base_day:   # review 2 (MUST 2): a Marg line dated the base count's day is in that count
                    if not (str(p.get("date") or "")[:10] == base_day and after_bills and _sf()._bill(p.get("bill")) in after_bills):   # S957: unless S956 adds it after
                        continue
                u = float(p.get("units") or 0)
                if u > 0:
                    cands.append(dict(units=u, bill=str(p.get("bill") or ""), vendor=str(p.get("supkey") or ""), day=str(p.get("date") or "")[:10]))
        best = None
        for c in cands:
            d = abs(short - c["units"])
            if d <= max(tol * c["units"], float(pk) / 2.0) and (best is None or d < best[0]):
                best = (d, c)
        if best is None:
            return None
        c = dict(best[1])
        bill = re.sub(r"^[Aa]0*", "", c["bill"].strip()) if c["bill"].strip() else ""
        day = dmy(c["day"])[:5] if c["day"] else ""
        who_when = ", ".join(x for x in (c["vendor"], day) if x)
        if bill:
            c["what"] = "bill %s (%s)" % (bill, who_when) if who_when else "bill %s" % bill
            c["what_hi"] = "bill %s (%s) ka maal" % (bill, who_when) if who_when else "bill %s ka maal" % bill
        else:
            c["what"] = "the delivery of %s" % (who_when or "these days")
            c["what_hi"] = "%s ka naya maal" % (who_when or "abhi aaya")
        c["why"] = "recount: was the carton of %s on the shelf?" % c["what"]
        c["why_hi"] = "Dobara giniye: pichhli ginti mein %s shayad gina nahi gaya. Uska carton bhi dekhkar poori ginti likhiye." % c["what_hi"]
        c["bill"] = bill
        return c
    except Exception:                                         # noqa: BLE001 -- the count is never refused for it
        return None


def _s936_hold_row(con, pid, H, note=None):
    """The point HELD for a recount: status 'recount', its note says why (first, so the owner's page shows it). No commit."""
    txt = "held for a recount -- short by about %s, not a loss" % H["what"]
    if note and str(note).startswith("Count now, to bill"):  # S934's prefix stays first (stock_check reads it)
        txt = str(note) + " · " + txt
    elif note:
        txt += " · " + str(note)
    con.execute("UPDATE stock_point SET status='recount', settled_at=NULL, note=? WHERE id=?", (txt, int(pid)))
    _s936_touch(con)
    _audit(con, "point_held_for_recount", dict(point_id=int(pid), delivery=dict(units=H.get("units"), bill=H.get("bill"), vendor=H.get("vendor"), day=H.get("day"))),
           "system", pid)
    return txt


def _s936_open_recount(con, P, who):
    """After a held count: ONE Count-now ask by itself (by 'system', recount_of the held point, the question for Darpan) -- unless one is
    already open for the item. Called by each caller AFTER its own ask closing (answer_roster, darpan_point, correct_roster, answer_now) and
    by _s934_settle. No commit. Fail-soft."""
    try:
        if not P or P.get("status") != "recount" or not P.get("hold"):
            return None
        if _s936_open_recount_ask(con, P["item"]) is not None:
            return None
        H = P["hold"]
        cur = con.execute("INSERT INTO stock_watch_ask (item_norm, item, by, at, mode, recount_of, why, why_hi) VALUES (?,?,?,?,?,?,?,?)",
                          (norm_name(P["item"]), P["item"], "system", now_iso(), "now", int(P["id"]), H.get("why") or "", H.get("why_hi") or ""))
        _audit(con, "recount_asked", dict(item=P["item"], held_point=int(P["id"]), why=H.get("why")), who or "system", cur.lastrowid)
        return int(cur.lastrowid)
    except sqlite3.Error:
        return None


def _s936_touch(con):
    """A held or recounted count changes a row's status, not stock_point's newest id: one 'count.' setting row is touched so the stock of
    record's fingerprint (it reads the count.% rows) rebuilds the record. Not a setting anyone sets: settings() never reads it. No commit."""
    try:
        con.execute("INSERT INTO setting (key, value, note) VALUES ('count._s936_held_at', ?, 'S936: moves when a count is held or recounted (the record rebuilds)') "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (dt.datetime.now().isoformat(),))
    except sqlite3.Error:
        pass


def _s936_sitting(con, who):
    """D1047: (bill, seconds since it was keyed) of the sitting -- the last sale bill `who` keyed with a Count now TODAY, within
    count.sitting_minutes of now; (None, None) otherwise (another person, another day, an older sitting)."""
    try:
        if not who:
            return None, None
        S = settings(con)
        lo = (dt.datetime.now() - dt.timedelta(minutes=int(S["sitting_minutes"]))).replace(microsecond=0).isoformat()
        r = con.execute("SELECT last_bill, at FROM stock_point WHERE by=? AND at>=? AND substr(at,1,10)=? AND COALESCE(last_bill,'')<>'' ORDER BY at DESC, id DESC LIMIT 1",
                        (who, lo, today().isoformat())).fetchone()
        if not r:
            return None, None
        try:
            age = max(0, int((dt.datetime.now() - dt.datetime.fromisoformat(str(r[1])[:19])).total_seconds()))
        except ValueError:
            age = int(S["sitting_minutes"]) * 60
        return _s934_bill_no(r[0]), age
    except sqlite3.Error:
        return None, None


def _s936_sitting_bill(con, who):
    """D1047: the sitting's bill number, or None."""
    return _s936_sitting(con, who)[0]



# ---- S976 (28-Nov-2026, Sanjeevni session 543, kit S976_WHOLE_UNIT_PACK; F-1742) ---------------------------------------------------------
#  Darpan's count screen for a whole-unit item (the desk's list, "CCM = bottle"): ONE box in its own word (Botal), like a gel's Tube --
#  never Patte / Goli with a pack of its packing (CCM 1*40 stored 40 per bottle on 28-11). item_info() gives such an item pack 1, so the
#  owner's asks, Abhi ginti, Stock batao and Kuchh gadbad hai read it whole; the day's morning list is put right after it is written
#  (a ranked or carried row keeps the pack it was written with). Every other item is exactly as before.
KIT_S976 = "S976_WHOLE_UNIT_PACK"


def _s976_whole(con, name):
    try:
        return _sf()._s976_whole(con, name)
    except Exception:                                         # noqa: BLE001
        return None


def _s976_pack(con, name, packing, pack=None):
    """The pack the count screen uses: 1 for a whole-unit item, else pack_of(packing) as before."""
    if _s976_whole(con, name):
        return 1
    return pack_of(packing, pack)


_item_info_before_s976 = item_info


def item_info(con, sp, name):                                 # noqa: F811 -- S976
    info = _item_info_before_s976(con, sp, name)
    if int(info.get("pack") or 1) > 1 and (_s976_whole(con, info.get("item") or name) or _s976_whole(con, name)):
        info = dict(info, pack=1)
    return info


def _s976_fix_day(con, day):
    """A whole-unit item's UNANSWERED rows of the day's morning list read pack 1 (a ranked or carried row was written with its packing's)."""
    n = 0
    try:
        for rid, item, pack in con.execute("SELECT id, item, pack FROM stock_spot_roster WHERE day=? AND answered_at IS NULL AND COALESCE(pack,1)>1",
                                           (str(day)[:10],)).fetchall():
            if _s976_whole(con, item):
                con.execute("UPDATE stock_spot_roster SET pack=1 WHERE id=? AND answered_at IS NULL", (rid,))
                n += 1
        if n:
            con.commit()
    except sqlite3.Error:
        pass
    return n


_build_roster_before_s976 = build_roster


def build_roster(con, day=None, S=None, sp=None, who="system", force=False, asks_ok=False):      # noqa: F811 -- S976
    V = _build_roster_before_s976(con, day, S, sp, who, force, asks_ok)
    if _s976_fix_day(con, (day or today()).isoformat()):
        return roster_view(con, day, S, sp)
    return V


_roster_view_before_s976 = roster_view


def roster_view(con, day=None, S=None, sp=None):              # noqa: F811 -- S976: the list's words read the whole-unit list first
    try:
        _s976_whole(con, "-")                                 # loads the desk's list into qty_words (Botal, never Patte)
    except Exception:                                         # noqa: BLE001
        pass
    return _roster_view_before_s976(con, day, S, sp)
# ---- S976 end ---------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "job":
        db = os.environ.get("FINANCE_DB") or os.path.join(HERE, "finance.db")
        if "--db" in args:
            db = args[args.index("--db") + 1]
        sys.exit(job(db))
    print("usage: stock_watch.py job [--db PATH]   (the 06:30 cron job: the day's roster, the plan, the arrivals)")
    sys.exit(2)
