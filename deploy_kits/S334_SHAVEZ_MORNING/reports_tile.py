"""
reports_tile.py -- "Aaj ki reports": Shavez's morning page, the Marg report generator's tile.
                   S243 (13-Sep-2026) -> S274 / kit S334_SHAVEZ_MORNING (20-Sep-2026).

THE OWNER'S RULING, 13-Sep-2026 (S243).  Shavez (portal login `shavez`) is the Marg REPORT GENERATOR --
a morning job on the medical PC, before any sale starts, and on Amir's days too.  The server sees each
report arrive through the one door (marg_take.take -> mi_file, the pushed-report staging, the purchase
push, the stock snapshot) within seconds; his page confirms each and prompts him ONLY for the refused
and the still-due ones.

THE OWNER'S RULING, 18/20-Sep-2026 (SHAVEZ_MORNING_TILE_PLAN, D567 item 1 and 2).  The same tile, made
into his MORNING page:
  * it opens on ONE thing -- "Kal ki bikri report aur closing stock nikaliye" -- with the Marg path and
    the settings, and the DATE it is for: yesterday, or the last day the counter sold (the counter is
    closed on Sundays -- measured, no Sunday sale day since July -- so on a Monday the date is Saturday);
  * a file that lands shows "aa gayi, jaanch ho rahi hai" (processing);  a TICK appears ONLY when the
    report re-adds under the spine's own certified readers (MARG_REPORT_CONTRACT_v1 s4.4 / s4.9): the
    reading /root/finance/spine/readings/<md5>.json written by spine_evidence.py, or -- for a report the
    door KEEPS on this box (the closing stock, the lists) -- the same reader run here on the kept file.
    A tick is never shown just because a file turned up; the door's own VERIFIED is the structural check;
  * a reading that FAILS its witness reads "dobara banaiye" with the reason in plain words;
  * both in -> "Aaj ka kaam poora"; both in since the night before -> "kal raat ho gaya";
  * the MISSED MORNING: from 10:00 on a counter day, if yesterday's pair has not arrived, a red banner --
    "Kal ki report baaki hai -- abhi mat nikaliye, counter par bikri shuru ho chuki hai" -- and the same
    line on the owner's card.  After 21:00 it turns to "Ab nikaliye".  The 10:00 / 21:00 rule stands
    until the medical-PC agent reports the day's first sale entry (plan s4); env REPORTS_SALE_START /
    REPORTS_SALE_END move them.  The banner never blames a person (attendance is not visible here yet);
  * on the 1st of a month (kept on the page until the 7th, or until they arrive): Stock valuation and
    Stock expiry as on the last day of the month before.  The spine has no reader for these two, so
    their tick is the door's format check and says so;
  * THE OWNER'S OWN THREE (item 2): the salt-wise list more than 8 days old, the category-wise or the
    item list more than 35 days old, is ONE quiet line on his card -- carried inside the same `line`
    the hub's Marg card already prints, so no other file changes.

PRINCIPLES (the same as Amir's page, D469): he is never asked whether a report arrived; nothing on this
page writes anything (one in-process cache of readings computed here, never a file); no JavaScript;
server-rendered HTML, phone first, Hinglish in Latin script; the page refreshes itself every 30 s.

THE OWNER sees the same status as ONE English line on the hub's Marg card (/finance/reports/aaj/api/status
-> `line`), now carrying the banner and the overdue lists when there are any.

GATE: any role on the medical unit (maker / checker / viewer), exactly as Amir's page.  Anonymous is sent
to the portal by finance_app's own before_request gate before this module is reached.

Nothing here writes to the database.  No table is created.  Every read is guarded against a table that
does not exist yet (the purchase, stock and marg_ingest tables are lazy, F-303), and against a spine that
is not there (then every tick waits, honestly, and the page says the spine has not read the file yet).
"""

import csv
import glob
import html
import io
import json
import os
import sqlite3
import sys
from datetime import date, datetime, timedelta, timezone

from flask import Blueprint, jsonify, redirect, request

bp = Blueprint("reports_tile", __name__)

_db = None
_require = None
_unit = "medical"
_roles = ("maker", "checker", "viewer")

IST = timezone(timedelta(hours=5, minutes=30))

# Where Amir's punches are read from -- the same two files export_watch.py reads (S240).
PUNCHES = os.environ.get("ATT_PUNCH_CSV", "/root/punches.csv")
STAFF_DB = os.environ.get("SR_DB_PATH", "/root/staff_register/staff_register.db")
AMIR_NAME = "Amir Sohail"
AMIR_MACHINE_ID = os.environ.get("AMIR_MACHINE_ID", "101")   # the fallback when the register cannot say

KIT = "S334_SHAVEZ_MORNING"

# purchase_export types that carry the item lines (either grouping counts, export_watch's rule)
PURCHASE_LINE_TYPES = ("ITEMWISE", "BILLITEMWISE")
MI_PURCHASE_LINE_TYPES = ("PURCHASE_ITEMWISE", "PURCHASE_BILLITEMWISE")

# S334 -- the spine (kit S331): its readings and its read door; the door's kept files.
SPINE_DIR = os.environ.get("SPINE_DIR", "/root/finance/spine")
SPINE_READINGS = os.environ.get("SPINE_READINGS", os.path.join(SPINE_DIR, "readings"))
SPINE_DB = os.environ.get("SPINE_DB", os.path.join(SPINE_DIR, "spine.db"))
MI_ARCHIVE = os.environ.get("MI_ARCHIVE", "/root/marg_ingest/archive")

# S334 -- the missed-morning rule, until the medical-PC agent reports the first sale (plan s4).
SALE_START = os.environ.get("REPORTS_SALE_START", "10:00")
SALE_END = os.environ.get("REPORTS_SALE_END", "21:00")

# S334 -- the owner's own three lists, and how old is overdue (plan s6).
OWNER_LISTS = (("SALT_WISE_ITEM_LIST", "salt list", 8),
               ("CATEGORY_WISE_ITEM_LIST", "category list", 35),
               ("ITEM_MASTER", "item list", 35))

# the families the spine's readers certify (marg_read.TITLES); mi_file type -> reader family
CERTIFIED = {"SALE_BILLWISE": "SALE_BILLWISE", "STOCK_CLOSING": "STOCK_CLOSING",
             "SALT_WISE_ITEM_LIST": "SALT_WISE_ITEM_LIST", "CATEGORY_WISE_ITEM_LIST": "CATEGORY_WISE_ITEM_LIST",
             "ITEM_MASTER": "ITEM_MASTER", "PURCHASE_BILLWISE": "PURCHASE_BILLWISE",
             "PURCHASE_ITEMWISE": "PURCHASE_LINES", "PURCHASE_BILLITEMWISE": "PURCHASE_LINES"}

_READ_CACHE = {}      # md5 -> reading computed here from a kept file (process lifetime; never a file)


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------

def _now():
    return datetime.now(IST)


def _today():
    return _now().date()


def _esc(v):
    return html.escape("" if v is None else str(v), quote=True)


def _table_exists(cx, name):
    return cx.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def _norm_ts(s):
    """Any of the estate's stamps -> 'YYYY-MM-DD HH:MM:SS' (IST as written), for comparing and showing."""
    s = (s or "").strip()
    if not s:
        return ""
    if len(s) >= 15 and s[8] == "-" and s[:8].isdigit():          # 20260913-091233
        return "%s-%s-%s %s:%s:%s" % (s[:4], s[4:6], s[6:8], s[9:11], s[11:13], s[13:15])
    s = s.replace("T", " ")
    if "+" in s[10:]:
        s = s[:s.index("+", 10)]
    return s[:19]


def _hhmm(s):
    n = _norm_ts(s)
    return n[11:16] if len(n) >= 16 else ""


def _ddmm(d):
    if isinstance(d, str):
        try:
            d = date.fromisoformat(d[:10])
        except ValueError:
            return d
    return d.strftime("%d-%m-%Y")


def _day_word(d):
    return ("Somvaar", "Mangalvaar", "Budhvaar", "Guruvaar", "Shukravaar", "Shanivaar", "Ravivaar")[d.weekday()]


def _hm(s, default):
    try:
        h, m = (s or default).split(":")
        return int(h) * 60 + int(m)
    except (ValueError, AttributeError):
        h, m = default.split(":")
        return int(h) * 60 + int(m)


def _due_day(today):
    """The day the morning pair is for: yesterday, or the last day the counter sold.  The counter is
    closed on Sundays (measured Jul-Sep 2026: no Sunday sale day), so a Monday's pair is Saturday's."""
    d = today - timedelta(days=1)
    while d.weekday() == 6:
        d -= timedelta(days=1)
    return d


def _month_last(today):
    """The last day of the month before `today`."""
    return today.replace(day=1) - timedelta(days=1)


# --------------------------------------------------------------------------
# the refusal reason, in plain Hindi
# --------------------------------------------------------------------------

def hindi_reason(reason, verdict=""):
    """The router's English reason -> one line a counter person can act on.  The English text is
    shown beneath it in small type, so nothing is hidden from the owner."""
    r = (reason or "").lower()
    v = (verdict or "").upper()
    if "empty" in r:
        return "File khali hai -- Marg me report dobara banaiye."
    if "not really" in r or "could not be read" in r or "unreadable" in r or "deep parse failed" in r:
        return "File padhi nahi ja saki -- desktop par khuli Excel band karke dobara export kijiye."
    if "no item detail" in r or "item deta" in r:
        return "Item detail nahi hai -- 'With Item Details = Yes' karke dobara banaiye."
    if "no signature" in r or v == "UNKNOWN":
        return "Ye report pehchan nahi aayi -- Marg me wahi report chuniye jo roz banti hai."
    if "wrong layout" in r or "header" in r or "layout" in r:
        return "Report ka format alag hai -- wahi report, wahi layout chuniye."
    if "date" in r or "tareekh" in r or "period" in r:
        return "Tareekh theek nahi hai -- kal ki tareekh (ya 1 tareekh se aaj tak) chuniye."
    if "truncat" in r or "arithmetic" in r or "total" in r or "end" in r or "incomplete" in r:
        return "Report poori nahi hai -- ant tak export kijiye, phir file band kijiye."
    if "column map" in r or "no days" in r or "source" in r:
        return "Server is file ko padh nahi paya -- dobara export kijiye; na ho to doctor sahab ko bataiye."
    if "not a marg export" in r or "extension" in r:
        return "Ye Marg ki export file nahi hai -- .xls file bhejiye."
    if "pc" in r and ("refus" in r or "reject" in r):
        return "Medical PC ne file manzoor nahi ki -- dobara banaiye."
    return "Server ne manzoor nahi kiya -- dobara banaiye; na ho to doctor sahab ko bataiye."


def hindi_failed(failed):
    """The spine reader's failed witness checks (marg_read check names) -> one line for the counter.
    The English names are shown beneath in small type."""
    f = " ".join(failed or []).lower()
    if "total" in f or "grand" in f or "sum" in f:
        return "Report ke total nahi milte -- Marg me poori report ant tak export kijiye, phir dobara banaiye."
    if "footer" in f or "bill count" in f:
        return "Report poori nahi aayi -- ant tak export kijiye (Excel band karke), phir dobara banaiye."
    if "serial" in f or "line numbers" in f or "classified" in f or "at row" in f:
        return "Report ki kuch lines padhi nahi gayi -- wahi report, wahi layout, dobara banaiye."
    if "date" in f:
        return "Report par tareekh nahi hai -- kal ki tareekh chun kar dobara banaiye."
    return "Jaanch me galti mili -- dobara banaiye; na ho to doctor sahab ko bataiye."


# --------------------------------------------------------------------------
# S334 -- the certification: the spine's readers
# --------------------------------------------------------------------------

def _reading_from_store(md5):
    """The evidence store's reading for this file, or None."""
    if not md5:
        return None
    p = os.path.join(SPINE_READINGS, md5 + ".json")
    try:
        with open(p, "r", encoding="utf-8") as fh:
            rec = json.load(fh)
    except (OSError, ValueError):
        return None
    if not rec.get("family"):
        return None                                   # a file the spine does not read: no certificate
    rec["_source"] = "spine"
    return rec


def _kept_path(server_name):
    """Where the door kept this file, if it kept it (the archive is laid out type/month/name)."""
    if not server_name or not os.path.isdir(MI_ARCHIVE):
        return None
    hits = glob.glob(os.path.join(MI_ARCHIVE, "**", server_name), recursive=True)
    hits = [h for h in hits if os.path.isfile(h) and not any(("%s%s" % (os.sep, x)) in h for x in ("_REFUSED", "_UNKNOWN", "_spool", "_outbox"))]
    return hits[0] if hits else None


def _reading_from_kept(md5, server_name):
    """The same certified reader (marg_read, kit S331) run here on a file the door KEPT; cached in
    memory by md5.  None when the file is not kept, or the reader is not installed."""
    if md5 in _READ_CACHE:
        return _READ_CACHE[md5]
    p = _kept_path(server_name)
    if not p:
        return None
    try:
        if SPINE_DIR not in sys.path:
            sys.path.insert(0, SPINE_DIR)
        import marg_read                                        # noqa: PLC0415
        rec = marg_read.reading_record(p, os.path.basename(p))
    except Exception:                                           # noqa: BLE001
        return None
    if not rec.get("family"):
        return None
    rec["_source"] = "local"
    _READ_CACHE[md5] = rec
    return rec


def certify(md5, server_name="", typ=""):
    """-> None (no certificate yet), or {'ok': bool, 'failed': [...], 'count': '24 bills', 'source': ...}."""
    if typ and typ not in CERTIFIED:
        return None
    rec = _reading_from_store(md5) or _reading_from_kept(md5, server_name)
    if rec is None:
        return None
    d = rec.get("data") or {}
    fam = rec.get("family") or ""
    if fam == "SALE_BILLWISE":
        count = "%d bills" % len(d.get("bills") or [])
    elif fam == "STOCK_CLOSING":
        count = "%d items" % len(d.get("items") or [])
    elif fam == "PURCHASE_BILLWISE":
        count = "%d bills" % len(d.get("bills") or [])
    elif fam == "PURCHASE_LINES":
        count = "%d lines" % len(d.get("lines") or [])
    else:
        n = d.get("n_items") or len(d.get("items") or d.get("groups") or [])
        count = ("%d items" % n) if n else ""
    return {"ok": bool(rec.get("ok")), "failed": list(rec.get("failed") or []), "count": count,
            "source": rec.get("_source", ""), "family": fam, "reader": rec.get("reader", "")}


# --------------------------------------------------------------------------
# what the server already holds
# --------------------------------------------------------------------------

def _mi_rows(cx, types, day_from=None, day_to=None, received_day=None):
    """mi_file rows of the given types (the marg_ingest / marg_take door).  Pure read."""
    if not _table_exists(cx, "mi_file"):
        return []
    q = ("SELECT md5, type, verdict, reason, pc_verdict, date_from, date_to, received_at, stamp, drive_name, server_name "
         "FROM mi_file WHERE type IN (%s)" % ",".join("?" * len(types)))
    args = list(types)
    if received_day:
        q += " AND substr(received_at,1,10)=?"
        args.append(received_day)
    q += " ORDER BY received_at DESC"
    out = []
    for r in cx.execute(q, args).fetchall():
        d = dict(r)
        if day_from is not None or day_to is not None:
            df, dto = (d.get("date_from") or "")[:10], (d.get("date_to") or "")[:10]
            if day_from is not None and (not dto or dto < day_from):
                continue
            if day_to is not None and (not df or df > day_to):
                continue
        out.append(d)
    return out


def _mi_refusals_today(cx, today_iso):
    """Every mi_file row received today that was not verified, newest first."""
    if not _table_exists(cx, "mi_file"):
        return []
    return [dict(r) for r in cx.execute(
        "SELECT md5, type, verdict, reason, pc_verdict, date_from, date_to, received_at, drive_name "
        "FROM mi_file WHERE substr(received_at,1,10)=? AND verdict<>'VERIFIED' "
        "ORDER BY received_at DESC", (today_iso,)).fetchall()]


def _pick(ok_rows, bad_rows, today_iso="", certified=True):
    """The state of one row.  A verified copy wins over an earlier refusal; the newest verified copy is
    the one certified.  States: ok (certified) · arrived (verified by the door, the spine has not read
    it yet) · bad (the reader's witness failed: dobara) · refused (the door refused) · due."""
    if ok_rows:
        best = max(ok_rows, key=lambda r: _norm_ts(r.get("received_at")))
        when = _norm_ts(best.get("received_at"))
        st = {"at": _hhmm(best.get("received_at")), "when": when,
              "night_before": bool(today_iso) and bool(when) and when[:10] < today_iso}
        if not certified:                                        # a row the spine has no reader for
            st.update(state="ok", cert="structural", count="")
            return st
        # the certificate comes from the newest copy the DOOR holds by md5 (a stock_feed / staging row
        # has none: it proves arrival, never the reading)
        with_md5 = [r for r in ok_rows if r.get("md5")]
        src = max(with_md5, key=lambda r: _norm_ts(r.get("received_at"))) if with_md5 else best
        c = certify(src.get("md5"), src.get("server_name"), src.get("type"))
        if c is None:
            st.update(state="arrived", cert="pending", count="")
        elif c["ok"]:
            st.update(state="ok", cert=c["source"], count=c["count"])
        else:
            st.update(state="bad", cert=c["source"], count=c["count"], failed=c["failed"],
                      reason=", ".join(c["failed"])[:300], reason_hi=hindi_failed(c["failed"]))
        return st
    if bad_rows:
        b = bad_rows[0]
        reason = b.get("reason") or ""
        verdict = b.get("verdict") or ""
        if not reason and (b.get("pc_verdict") or "").upper() not in ("", "VERIFIED"):
            reason = "the medical PC refused it (%s)" % b.get("pc_verdict")
        return {"state": "refused", "at": _hhmm(b.get("received_at")), "when": _norm_ts(b.get("received_at")),
                "verdict": verdict, "reason": reason, "reason_hi": hindi_reason(reason, verdict)}
    return {"state": "due"}


def _sale_row(cx, y_iso, today_iso):
    ok = [r for r in _mi_rows(cx, ("SALE_BILLWISE",), day_from=y_iso, day_to=y_iso) if r["verdict"] == "VERIFIED"]
    if not ok and _table_exists(cx, "marg_push_staging"):
        # the pushed-report door (the older route the medical PC still uses)
        for r in cx.execute("SELECT received_at FROM marg_push_staging WHERE status<>'rejected' "
                            "AND survey_json LIKE ? ORDER BY received_at DESC LIMIT 1",
                            ('%"' + y_iso + '"%',)).fetchall():
            ok.append({"received_at": r["received_at"], "type": "SALE_BILLWISE"})
    bad = [r for r in _mi_rows(cx, ("SALE_BILLWISE",), received_day=today_iso) if r["verdict"] != "VERIFIED"]
    if not bad:
        bad = [r for r in _mi_rows(cx, ("SALE_BILLWISE",), day_from=y_iso, day_to=y_iso) if r["verdict"] != "VERIFIED"]
    if not bad and _table_exists(cx, "marg_push_staging"):
        for r in cx.execute("SELECT received_at, survey_json, filename_hint FROM marg_push_staging "
                            "WHERE status='rejected' AND substr(received_at,1,10)=? "
                            "ORDER BY received_at DESC LIMIT 1", (today_iso,)).fetchall():
            why = ""
            try:
                why = (json.loads(r["survey_json"] or "{}") or {}).get("error") or ""
            except Exception:                                  # noqa: BLE001
                why = ""
            bad.append({"received_at": r["received_at"], "verdict": "REFUSED", "reason": why, "pc_verdict": ""})
    st = _pick(ok, bad, today_iso)
    st.update(key="SALE_BILLWISE", label="Bill-wise sale report", pair=True,
              hint="%s ki (Bill Wise Statement, Report Type DETAIL, With Item Details YES)" % _ddmm(y_iso))
    return st


def _stock_row(cx, y_iso, today_iso):
    # Marg's "as on" is date_from.  Yesterday's close = as on the due day, or any later day up to this
    # morning (a closing taken before the counter opens); export_watch's rule.
    ok = [r for r in _mi_rows(cx, ("STOCK_CLOSING",))
          if r["verdict"] == "VERIFIED" and y_iso <= (r.get("date_from") or "")[:10] <= today_iso
          and (r.get("received_at") or "")[:10] >= y_iso]
    if _table_exists(cx, "stock_feed"):
        for as_on in (date.fromisoformat(y_iso).strftime("%d-%m-%Y"), date.fromisoformat(today_iso).strftime("%d-%m-%Y")):
            r = cx.execute("SELECT MIN(received_at) AS at, COUNT(*) AS n FROM stock_feed WHERE as_on=? "
                           "AND source LIKE 'push_snapshot%'", (as_on,)).fetchone()
            if r and r["n"] and (r["at"] or "")[:10] >= y_iso:
                ok.append({"received_at": r["at"], "type": "STOCK_CLOSING"})
    bad = [r for r in _mi_rows(cx, ("STOCK_CLOSING",), received_day=today_iso) if r["verdict"] != "VERIFIED"]
    st = _pick(ok, bad, today_iso)
    st.update(key="STOCK_CLOSING", label="Closing stock report", pair=True,
              hint="%s shaam tak ka (Closing Stock, poore store, Totals)" % _ddmm(y_iso))
    return st


def _month_rows(cx, today):
    """S334 -- on the 1st (kept until the 7th, or until they arrive): valuation and expiry as on the last
    day of the month before.  The spine has no reader for these two: the tick is the door's format check."""
    if not 1 <= today.day <= 7:
        return []
    last = _month_last(today)
    first_iso = today.replace(day=1).isoformat()
    out = []
    for typ, label, hint in (("STOCK_VALUATION", "Stock valuation", "Stock Valuation, %s tak ka" % _ddmm(last)),
                             ("STOCK_EXPIRY", "Stock expiry", "Stock Expiry, %s tak ka" % _ddmm(last))):
        rows = _mi_rows(cx, (typ,))
        ok = [r for r in rows if r["verdict"] == "VERIFIED" and (r.get("received_at") or "")[:10] >= first_iso
              and (r.get("date_from") or "")[:10] >= last.isoformat()]
        bad = [r for r in rows if r["verdict"] != "VERIFIED" and (r.get("received_at") or "")[:10] >= first_iso]
        st = _pick(ok, bad, today.isoformat(), certified=False)
        if st["state"] == "ok":
            st["note"] = "format jaanch (spine ye report nahi padhta)"
        st.update(key=typ, label=label, hint=hint, monthly=True)
        out.append(st)
    return out


def _purchase_rows(cx, y_iso, today_iso):
    """The daily pair, month-to-date, received today.  export_watch's coverage rule.  (Amir's rows are
    structural here as before -- his own tile is where his work is confirmed.)"""
    today = date.fromisoformat(today_iso)
    first = today.replace(day=1).isoformat()
    need_to = y_iso
    if today.day == 1:
        first = today_iso
        need_to = today_iso
    ymd = today.strftime("%Y%m%d")

    def pe(types):
        if not _table_exists(cx, "purchase_export"):
            return []
        out = []
        for r in cx.execute("SELECT type, period_from, period_to, export_stamp, received_at FROM purchase_export "
                            "WHERE type IN (%s) AND (substr(export_stamp,1,8)=? OR substr(received_at,1,10)=?)"
                            % ",".join("?" * len(types)), list(types) + [ymd, today_iso]).fetchall():
            d = dict(r)
            if (d.get("period_from") or "9")[:10] <= first and (d.get("period_to") or "")[:10] >= need_to:
                out.append({"received_at": d.get("received_at") or _norm_ts(d.get("export_stamp"))})
        return out

    def mi(types):
        rows = _mi_rows(cx, types, received_day=today_iso)
        ok = [r for r in rows if r["verdict"] == "VERIFIED"
              and (r.get("date_from") or "9")[:10] <= first and (r.get("date_to") or "")[:10] >= need_to]
        bad = [r for r in rows if r["verdict"] != "VERIFIED"]
        return ok, bad

    out = []
    ok_mi, bad_mi = mi(MI_PURCHASE_LINE_TYPES)
    st = _pick(pe(PURCHASE_LINE_TYPES) + ok_mi, bad_mi, certified=False)
    st.update(key="PURCHASE_ITEMWISE", label="Purchase item-wise report",
              hint="1 tareekh se aaj tak (Amir ke din)")
    out.append(st)
    ok_mi, bad_mi = mi(("PURCHASE_BILLWISE",))
    st = _pick(pe(("BILLWISE",)) + ok_mi, bad_mi, certified=False)
    st.update(key="PURCHASE_BILLWISE", label="Purchase bill-wise report",
              hint="1 tareekh se aaj tak (Amir ke din)")
    out.append(st)
    return out


def _salt_row(cx, today_iso):
    """Shown only when the salt refresh is due (a tick newer than the last list), or when a list
    arrived today.  Returns None when the row does not belong on today's page."""
    last_ok = ""
    rows = _mi_rows(cx, ("SALT_WISE_ITEM_LIST",))
    oks = [r for r in rows if r["verdict"] == "VERIFIED"]
    if oks:
        last_ok = max(_norm_ts(r.get("received_at")) for r in oks)
    newest_tick = ""
    if _table_exists(cx, "purchase_salt_task"):
        r = cx.execute("SELECT MAX(done_at) AS t FROM purchase_salt_task WHERE COALESCE(done,0)=1 "
                       "AND done_at IS NOT NULL AND done_at<>''").fetchone()
        newest_tick = _norm_ts(r["t"]) if r and r["t"] else ""
    due = bool(newest_tick) and (not last_ok or newest_tick > last_ok)
    arrived_today = bool(last_ok) and last_ok[:10] == today_iso
    if not due and not arrived_today:
        return None
    ok = [r for r in oks if _norm_ts(r.get("received_at"))[:10] == today_iso] if arrived_today else []
    bad = [r for r in rows if r["verdict"] != "VERIFIED" and (r.get("received_at") or "")[:10] == today_iso]
    st = _pick(ok, bad, today_iso)
    st.update(key="SALT_WISE_ITEM_LIST", label="Salt-wise item list",
              hint="salt ka kaam hua hai -- nayi list chahiye" if due else "aaj aayi")
    return st


# --------------------------------------------------------------------------
# S334 -- the owner's own three lists: one quiet line when one is overdue
# --------------------------------------------------------------------------

def _spine_last_as_on(family):
    """The newest as-on the spine holds for a list family that passed its witness, from sp_export
    (read-only), or '' when the spine is not there."""
    try:
        con = sqlite3.connect("file:%s?mode=ro" % SPINE_DB, uri=True)
        try:
            r = con.execute("SELECT MAX(COALESCE(NULLIF(as_on,''), NULLIF(date_to,''), substr(stamp,1,4)||'-'||substr(stamp,5,2)||'-'||substr(stamp,7,2))) "
                            "FROM sp_export WHERE family=? AND ok=1", (family,)).fetchone()
            return (r[0] or "")[:10] if r else ""
        finally:
            con.close()
    except sqlite3.Error:
        return ""


def owner_lists(cx, today):
    """-> [{'key','label','last','age_days','limit','overdue'}] for the salt, category and item lists.
    The newest of: the spine's certified reading, or the door's VERIFIED copy (as-on = date_from, else
    the day it arrived)."""
    out = []
    for typ, label, limit in OWNER_LISTS:
        last = _spine_last_as_on(typ)
        for r in _mi_rows(cx, (typ,)):
            if r["verdict"] != "VERIFIED":
                continue
            d = (r.get("date_from") or "")[:10] or (r.get("received_at") or "")[:10]
            if d and d > last:
                last = d
        age = None
        if last:
            try:
                age = (today - date.fromisoformat(last)).days
            except ValueError:
                age = None
        out.append({"key": typ, "label": label, "last": last, "age_days": age, "limit": limit,
                    "overdue": age is None or age > limit})
    return out


# --------------------------------------------------------------------------
# is today an Amir day?
# --------------------------------------------------------------------------

def _punched_today(today):
    """export_watch.py's own punch logic when it is importable (same folder as finance_app);
    otherwise the same reading done here.  None when the punch file cannot be read."""
    sid = None
    try:
        import export_watch                                    # noqa: PLC0415
        try:
            sid, _where = export_watch.staff_id_for(AMIR_NAME, STAFF_DB, None)
        except Exception:                                      # noqa: BLE001
            sid = None
        sid = sid or AMIR_MACHINE_ID
        return export_watch.punched_on(sid, today, PUNCHES)
    except Exception:                                          # noqa: BLE001
        pass
    sid = sid or AMIR_MACHINE_ID
    d = today.isoformat()
    try:
        with io.open(PUNCHES, "r", encoding="utf-8-sig", errors="replace", newline="") as fh:
            for r in csv.reader(fh):
                if len(r) >= 2 and r[0].strip() == str(sid) and r[1].strip()[:10] == d:
                    return True
    except OSError:
        return None
    return False


def _amir_day(cx, today):
    if _table_exists(cx, "amir_day"):
        if cx.execute("SELECT 1 FROM amir_day WHERE day=?", (today.isoformat(),)).fetchone():
            return True, "amir_day"
    if _punched_today(today):
        return True, "punch"
    return False, ""


# --------------------------------------------------------------------------
# S334 -- the missed morning
# --------------------------------------------------------------------------

def _banner(rows, today, now):
    """None, or {'kind': 'missed'|'now', 'text_hi', 'text_en'}.  The pair (sale + closing) counts as in
    when the door has it (arrived / ok / bad -- he did export; the spine decides the tick).  On a Sunday
    the counter is closed, so nothing is 'not now'."""
    pair = [r for r in rows if r.get("pair")]
    missing = [r for r in pair if r["state"] in ("due", "refused")]
    if not missing or today.weekday() == 6:
        return None
    mins = now.hour * 60 + now.minute
    if mins < _hm(SALE_START, "10:00"):
        return None
    what = " aur ".join("bikri report" if r["key"] == "SALE_BILLWISE" else "closing stock" for r in missing)
    if mins < _hm(SALE_END, "21:00"):
        return {"kind": "missed",
                "text_hi": "Kal ki %s baaki hai -- abhi mat nikaliye, counter par bikri shuru ho chuki hai. "
                           "Counter band hone ke baad (%s ke baad) nikaliye." % (what, SALE_END),
                "text_en": "MISSED: yesterday's %s not in by %s -- not to be exported while the counter sells; after %s"
                           % (" and ".join("sale report" if r["key"] == "SALE_BILLWISE" else "closing stock" for r in missing),
                              SALE_START, SALE_END)}
    return {"kind": "now",
            "text_hi": "Ab nikaliye -- kal ki %s abhi tak nahi aayi. Counter band hai, koi bhi nikaal sakta hai." % what,
            "text_en": "NOW: yesterday's %s still not in -- the counter is closed, anyone may export it"
                       % " and ".join("sale report" if r["key"] == "SALE_BILLWISE" else "closing stock" for r in missing)}


# --------------------------------------------------------------------------
# the day, gathered once
# --------------------------------------------------------------------------

def status(cx, today=None, now=None):
    now = now or _now()
    today = today or now.date()
    today_iso = today.isoformat()
    due = _due_day(today)
    y_iso = due.isoformat()
    amir, amir_why = _amir_day(cx, today)
    rows = [_sale_row(cx, y_iso, today_iso), _stock_row(cx, y_iso, today_iso)]
    rows += _month_rows(cx, today)
    if amir:
        rows += _purchase_rows(cx, y_iso, today_iso)
    salt = _salt_row(cx, today_iso)
    if salt:
        rows.append(salt)
    # files the server could not place at all today (no type): said once, at the end
    unknown = [r for r in _mi_refusals_today(cx, today_iso)
               if (r.get("type") or "") in ("", "_UNKNOWN", "UNKNOWN")]
    certified = sum(1 for r in rows if r["state"] == "ok")
    arrived = sum(1 for r in rows if r["state"] in ("ok", "arrived", "bad"))
    pending = sum(1 for r in rows if r["state"] == "arrived")
    bad = sum(1 for r in rows if r["state"] == "bad")
    refused = sum(1 for r in rows if r["state"] == "refused")
    total = len(rows)
    pair = [r for r in rows if r.get("pair")]
    pair_in = all(r["state"] in ("ok", "arrived", "bad") for r in pair)
    night_before = pair_in and all(r.get("night_before") for r in pair)
    banner = _banner(rows, today, now)
    lists = owner_lists(cx, today)
    overdue = [l for l in lists if l["overdue"]]
    line = "Today's reports: %d of %d arrived" % (arrived, total)
    if pending:
        line += ", %d awaiting the spine's check" % pending
    if bad:
        line += ", %d FAILED the check (redo)" % bad
    if refused:
        line += ", %d refused" % refused
    if banner:
        line += " · " + banner["text_en"]
    if overdue:
        line += " · OVERDUE: " + ", ".join(
            ("%s %d days" % (l["label"], l["age_days"])) if l["age_days"] is not None else ("%s never" % l["label"])
            for l in overdue)
    return {"ok": True, "kit": KIT, "day": today_iso, "yesterday": y_iso, "due_day": y_iso,
            "amir_day": amir, "amir_why": amir_why,
            "rows": rows, "arrived": arrived, "certified": certified, "pending": pending, "bad": bad,
            "refused": refused, "total": total, "all_in": arrived == total and bad == 0,
            "all_certified": certified == total, "pair_in": pair_in, "night_before": night_before,
            "banner": banner, "owner_lists": lists, "overdue": [l["key"] for l in overdue],
            "unknown_today": [{"at": _hhmm(u.get("received_at")), "reason": u.get("reason") or "",
                               "reason_hi": hindi_reason(u.get("reason"), u.get("verdict"))} for u in unknown[:3]],
            "line": line, "at": now.strftime("%Y-%m-%d %H:%M:%S")}


# --------------------------------------------------------------------------
# rendering -- Amir's page style, no JavaScript
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
.line{padding:12px 0;border-bottom:1px solid var(--line)}
.line:last-child{border-bottom:0}
.big{font-size:17px;font-weight:600}
.good{color:var(--ok)}
.bad{color:var(--bad)}
.due{color:var(--warn)}
.wait{color:var(--accent)}
.small{color:var(--soft);font-size:13px}
.state{display:block;margin-top:2px;font-size:16px}
.why{display:block;margin-top:6px;padding:10px;background:#fff8e1;border:1px solid #f0e0a8;border-radius:8px}
.done{background:#e7f3e9;border-color:#bfe0c6}
.banner{padding:14px;border-radius:10px;margin:0 0 14px;font-size:17px;font-weight:600;color:#fff}
.banner.missed{background:var(--bad)}
.banner.now{background:var(--accent)}
.how{background:#f3f6fa;border:1px solid #d9e2ee;border-radius:8px;padding:10px 12px;margin:8px 0 0;font-size:14px}
.how b{color:var(--accent)}
.foot{color:var(--soft);font-size:13px;margin:16px 0 0;text-align:center}
.btn{display:block;width:100%;padding:12px 16px;font-size:16px;font-weight:600;border-radius:10px;
     border:1px solid var(--accent);background:#fff;color:var(--accent);text-align:center;text-decoration:none}
"""


def _shell(title, body, refresh=30):
    meta = ("<meta http-equiv=refresh content='%d'>" % int(refresh)) if refresh else ""
    return ("<!doctype html><html lang=hi><head><meta charset=utf-8>"
            "<meta name=viewport content='width=device-width,initial-scale=1'>%s"
            "<title>%s</title><style>%s</style></head><body><div class=wrap>%s"
            "</div></body></html>" % (meta, _esc(title), _CSS, body))


def _denied():
    return _shell("Nahin khul saka",
                  "<div class=card><h2>Yeh page aapke liye nahin hai</h2>"
                  "<p>Apne login se kholiye, ya doctor sahab ko bataiye.</p>"
                  "</div>", refresh=0), 403


def _row_html(r):
    at = _esc(r.get("at", ""))
    when = ("kal raat %s baje" % at) if r.get("night_before") else ("%s baje" % at)
    if r["state"] == "ok":
        count = (" &middot; %s" % _esc(r["count"])) if r.get("count") else ""
        note = (" <span class=small>(%s)</span>" % _esc(r["note"])) if r.get("note") else ""
        state = ("<span class='state good'>&#10003; aa gayi, jaanch poori <span class=small>%s%s</span>%s</span>"
                 % (when, count, note))
    elif r["state"] == "arrived":
        state = ("<span class='state wait'>&#8987; aa gayi <span class=small>%s</span> &middot; jaanch ho rahi hai&hellip;"
                 "<br><span class=small>Server file ko padh kar total mila raha hai. Aap doosri report shuru kar sakte hain.</span></span>"
                 % when)
    elif r["state"] == "bad":
        state = ("<span class='state bad'>&#10007; jaanch me fail <span class=small>%s</span></span>"
                 "<span class=why>%s<br><span class=small>%s</span></span>"
                 % (when, _esc(r.get("reason_hi", "")), _esc(r.get("reason", ""))))
    elif r["state"] == "refused":
        state = ("<span class='state bad'>&#10007; manzoor nahi <span class=small>%s baje</span></span>"
                 "<span class=why>%s<br><span class=small>%s</span></span>"
                 % (at, _esc(r.get("reason_hi", "")), _esc(r.get("reason", ""))))
    else:
        state = "<span class='state due'>&#9675; baaki</span>"
    return ("<div class=line><span class=big>%s</span> <span class=small>%s</span>%s</div>"
            % (_esc(r["label"]), _esc(r.get("hint", "")), state))


def _how_block(s):
    """Step 1 -- what to do, with the Marg path and the settings, for the due day.  Shown while the
    pair is not in; after that the rows say everything."""
    due = _ddmm(s["due_day"])
    return ("<div class=how>"
            "<b>1.</b> Marg &rarr; Daily Reports &rarr; Sale Reports &rarr; <b>BILL WISE STATEMENT</b> &middot; "
            "tareekh <b>%s</b> &middot; Report Type <b>Detail</b> &middot; With Item Details <b>Yes</b> &rarr; Excel export.<br>"
            "<b>2.</b> Marg &rarr; Stock Reports &rarr; <b>Closing Stock</b> &middot; <b>poore store, Totals</b> &middot; "
            "as on <b>%s</b> &rarr; Excel export.<br>"
            "<span class=small>File yahan khud aa jaati hai -- kuch bhejna nahi hai. Excel khuli ho to pehle band kijiye.</span>"
            "</div>" % (due, due))


def render(s, picked_date=False):
    d = date.fromisoformat(s["day"])
    head = ("<h1>Aaj ki reports</h1><p class=sub>%s, %s%s</p>"
            % (_day_word(d), _ddmm(d), " &middot; Amir ka din" if s["amir_day"] else ""))
    body = head
    b = s.get("banner")
    if b:
        body += "<div class='banner %s'>%s</div>" % (_esc(b["kind"]), _esc(b["text_hi"]))
    if s["pair_in"]:
        if s["night_before"]:
            lead = "<p class='big good'>Kal raat ho gaya -- dono reports pehle hi aa gayi hain.</p>"
        else:
            lead = "<p class=big>Dono reports aa gayi hain -- neeche jaanch dekhiye.</p>"
    else:
        lead = ("<p class=big>%s ki bikri report aur closing stock nikaliye.</p>" % _esc(_ddmm(s["due_day"]))) + _how_block(s)
    rows = "".join(_row_html(r) for r in s["rows"])
    body += lead + "<div class=card>" + rows + "</div>"
    if s["unknown_today"]:
        u = s["unknown_today"][0]
        body += ("<div class='card'><div class=line><span class='big bad'>&#10007; Ek file pehchan nahi aayi "
                 "<span class=small>%s baje</span></span><span class=why>%s<br><span class=small>%s</span></span>"
                 "</div></div>" % (_esc(u["at"]), _esc(u["reason_hi"]), _esc(u["reason"])))
    if s["all_certified"] and s["total"]:
        body += "<div class='card done'><p class='big good' style='margin:0'>&#10003; Aaj ka kaam poora -- sab reports aa gayi aur jaanch poori.</p></div>"
    elif s["all_in"] and s["total"]:
        body += ("<div class='card'><p class='big wait' style='margin:0'>&#8987; Sab reports aa gayi; %d ki jaanch abhi chal rahi hai.</p></div>"
                 % s["pending"])
    else:
        body += ("<p class=foot>%d / %d aa gayi &middot; %d jaanch poori</p>" % (s["arrived"], s["total"], s["certified"]))
    if picked_date:
        body += "<p><a class=btn href='/finance/reports/aaj'>Aaj par wapas</a></p>"
    return _shell("Aaj ki reports", body, refresh=30 if not picked_date else 0)


# --------------------------------------------------------------------------
# routes
# --------------------------------------------------------------------------

def _gate():
    u, err = _require(*_roles, unit=_unit)
    return u, err


@bp.route("/finance/reports/aaj")
def page_today():
    u, err = _gate()
    if err:
        return _denied()
    cx = _db()
    return render(status(cx, _today()))


@bp.route("/finance/reports/aaj/<day>")
def page_day(day):
    u, err = _gate()
    if err:
        return _denied()
    try:
        d = date.fromisoformat(day[:10])
    except ValueError:
        return redirect("/finance/reports/aaj", code=302)
    cx = _db()
    return render(status(cx, d), picked_date=(d != _today()))


@bp.route("/finance/reports/aaj/api/status")
def api_status():
    u, err = _gate()
    if err:
        return jsonify(ok=False, error="not_permitted",
                       message="Your login has no role on this unit."), 403
    day = request.args.get("d") or ""
    try:
        d = date.fromisoformat(day[:10]) if day else _today()
    except ValueError:
        d = _today()
    cx = _db()
    return jsonify(status(cx, d))


@bp.route("/finance/reports/aaj/api/healthz")
def healthz():
    return {"ok": True, "kit": KIT, "at": _now().strftime("%Y-%m-%d %H:%M:%S")}


def init(app, db_getter, require_fn, unit="medical", roles=("maker", "checker", "viewer"), url_prefix=""):
    global _db, _require, _unit, _roles
    _db, _require, _unit, _roles = db_getter, require_fn, unit, tuple(roles)
    app.register_blueprint(bp, url_prefix=url_prefix)
    return bp


# --------------------------------------------------------------------------
# selftest -- the arithmetic on an in-memory db and a scratch readings folder, no Flask
# --------------------------------------------------------------------------

def selftest():
    import tempfile
    global SPINE_READINGS, SPINE_DB, MI_ARCHIVE
    fails = []
    n_checks = [0]

    def ck(n, c):
        n_checks[0] += 1
        print(("  ok   " if c else "  FAIL ") + n)
        if not c:
            fails.append(n)
    tmp = tempfile.mkdtemp(prefix="rt_selftest_")
    SPINE_READINGS = os.path.join(tmp, "readings")
    SPINE_DB = os.path.join(tmp, "spine.db")                    # absent: the owner's lists fall back to mi_file
    MI_ARCHIVE = os.path.join(tmp, "archive")                   # absent: nothing is read locally
    os.makedirs(SPINE_READINGS)
    _READ_CACHE.clear()

    def reading(md5, family, ok, failed=(), **data):
        with open(os.path.join(SPINE_READINGS, md5 + ".json"), "w") as fh:
            json.dump(dict(md5=md5, family=family, ok=ok, failed=list(failed), reader="S331.1", data=data), fh)

    cx = sqlite3.connect(":memory:")
    cx.row_factory = sqlite3.Row
    today = date(2026, 9, 15)                                   # a Tuesday
    y = "2026-09-14"
    at = lambda h, m=0: datetime(2026, 9, 15, h, m, tzinfo=IST)  # noqa: E731
    s = status(cx, today, at(8))
    ck("empty db: two rows, both due, nothing crashes", s["total"] == 2 and all(r["state"] == "due" for r in s["rows"]))
    ck("the due day is yesterday on a Tuesday", s["due_day"] == y)
    ck("owner's line reads 0 of 2 plus the three lists never seen",
       s["line"].startswith("Today's reports: 0 of 2 arrived") and "OVERDUE: salt list never, category list never, item list never" in s["line"])
    ck("no banner before 10:00", s["banner"] is None)
    s = status(cx, today, at(10, 5))
    ck("red banner from 10:00 when the pair is not in, and it names both",
       s["banner"] and s["banner"]["kind"] == "missed" and "bikri report aur closing stock" in s["banner"]["text_hi"] and "MISSED" in s["line"])
    s = status(cx, today, at(21, 30))
    ck("after 21:00 the banner turns to Ab nikaliye", s["banner"] and s["banner"]["kind"] == "now")
    ck("a Monday's due day is Saturday (the counter is closed on Sundays)", _due_day(date(2026, 9, 14)) == date(2026, 9, 12))
    ck("a Sunday shows no banner", status(cx, date(2026, 9, 13), datetime(2026, 9, 13, 12, tzinfo=IST))["banner"] is None)
    cx.executescript("""
      CREATE TABLE mi_file (md5 TEXT PRIMARY KEY, drive_id TEXT DEFAULT '', drive_name TEXT DEFAULT '', drive_folder TEXT DEFAULT '',
        drive_mtime TEXT DEFAULT '', size INTEGER DEFAULT 0, stamp TEXT DEFAULT '', type TEXT DEFAULT '', variant TEXT DEFAULT '',
        date_from TEXT DEFAULT '', date_to TEXT DEFAULT '', verdict TEXT DEFAULT '', reason TEXT DEFAULT '', server_name TEXT DEFAULT '',
        kept INTEGER DEFAULT 0, lines INTEGER DEFAULT 0, pc_type TEXT DEFAULT '', pc_verdict TEXT DEFAULT '', agree TEXT DEFAULT '',
        received_at TEXT NOT NULL, source TEXT DEFAULT '');
      CREATE TABLE purchase_export (md5 TEXT PRIMARY KEY, type TEXT, file TEXT, period_from TEXT, period_to TEXT, export_stamp TEXT,
        received_at TEXT, n_rows INTEGER, grand_amount_p INTEGER, superseded_by TEXT);
      CREATE TABLE purchase_salt_task (id INTEGER PRIMARY KEY, section TEXT, seq INTEGER, a TEXT, b TEXT, c TEXT, done INTEGER DEFAULT 0,
        done_by TEXT, done_at TEXT, answer TEXT, answer_by TEXT, answer_at TEXT, source_md5 TEXT, pushed_at TEXT);
      CREATE TABLE amir_day (day TEXT PRIMARY KEY, opened_at TEXT, closed_at TEXT, closed_by TEXT);
      CREATE TABLE stock_feed (id INTEGER PRIMARY KEY, as_on TEXT, source TEXT, item TEXT, qty INTEGER, received_at TEXT);
    """)
    cx.execute("INSERT INTO mi_file (md5,type,date_from,date_to,verdict,reason,received_at) VALUES ('a','SALE_BILLWISE',?,?,'REFUSED','deep parse failed: truncated',?)",
               (y, y, "2026-09-15T09:01:00+05:30"))
    s = status(cx, today, at(9, 2))
    ck("a refused sale report shows refused with a Hindi reason",
       s["rows"][0]["state"] == "refused" and "Excel" in s["rows"][0]["reason_hi"] and s["rows"][0]["at"] == "09:01")
    cx.execute("INSERT INTO mi_file (md5,type,date_from,date_to,verdict,received_at) VALUES ('b','SALE_BILLWISE',?,?,'VERIFIED',?)",
               (y, y, "2026-09-15T09:07:30+05:30"))
    s = status(cx, today, at(10, 30))
    ck("a later verified copy wins, but with no reading it is ARRIVED (processing), not a tick",
       s["rows"][0]["state"] == "arrived" and s["rows"][0]["at"] == "09:07" and s["certified"] == 0 and s["arrived"] == 1)
    ck("an arrived sale report is not 'missed' -- the banner names only the closing stock",
       s["banner"] and "closing stock" in s["banner"]["text_hi"] and "bikri report" not in s["banner"]["text_hi"])
    ck("the owner's line says one awaits the spine", "1 awaiting the spine's check" in s["line"])
    reading("b", "SALE_BILLWISE", False, failed=["GRAND TOTAL = sum of bill GROSS"], bills=[{}] * 24)
    s = status(cx, today, at(10, 30))
    ck("a reading that failed its witness reads BAD with a Hindi reason (dobara)",
       s["rows"][0]["state"] == "bad" and "total" in s["rows"][0]["reason_hi"].lower() and "FAILED" in s["line"])
    os.remove(os.path.join(SPINE_READINGS, "b.json"))
    _READ_CACHE.clear()
    reading("b", "SALE_BILLWISE", True, bills=[{}] * 24)
    s = status(cx, today, at(10, 30))
    ck("a reading that passed -> the tick, with its count", s["rows"][0]["state"] == "ok" and s["rows"][0]["count"] == "24 bills"
       and s["rows"][0]["cert"] == "spine")
    cx.execute("INSERT INTO stock_feed (as_on,source,item,qty,received_at) VALUES ('15-09-2026','push_snapshot','X',1,'2026-09-15T09:09:00')")
    s = status(cx, today, at(10, 30))
    ck("a morning stock snapshot as on today counts as yesterday's close -- arrived, awaiting the reader (no md5 to certify)",
       s["rows"][1]["state"] == "arrived" and s["banner"] is None and s["pair_in"])
    cx.execute("INSERT INTO mi_file (md5,type,date_from,date_to,verdict,server_name,received_at) VALUES ('c','STOCK_CLOSING',?,?,'VERIFIED','STOCK_CLOSING_TOTALS__x.xls',?)",
               (today.isoformat(), today.isoformat(), "2026-09-15T09:12:00+05:30"))
    reading("c", "STOCK_CLOSING", True, items=[{}] * 374, printed_total=1, lines_total=1)
    s = status(cx, today, at(10, 30))
    ck("the closing stock as on this morning, read by the spine -> tick, 374 items",
       s["rows"][1]["state"] == "ok" and s["rows"][1]["count"] == "374 items")
    cx.execute("INSERT INTO stock_feed (as_on,source,item,qty,received_at) VALUES ('15-09-2026','push_snapshot','Y',1,'2026-09-15T09:20:00')")
    s = status(cx, today, at(10, 30))
    ck("a later stock_feed row (no md5) does not hide the certificate of the door's copy",
       s["rows"][1]["state"] == "ok" and s["rows"][1]["count"] == "374 items")
    cx.execute("DELETE FROM stock_feed WHERE item='Y'")
    s = status(cx, today, at(10, 30))
    ck("both certified -> all_certified, no Amir row, no salt row yet", s["total"] == 2 and s["all_certified"] and s["all_in"])
    ck("owner's line: 2 of 2 arrived, no banner, lists still overdue", s["line"].startswith("Today's reports: 2 of 2 arrived · OVERDUE"))
    # the night before
    cx.execute("UPDATE mi_file SET received_at='2026-09-14T22:40:00+05:30' WHERE md5 IN ('b','c')")
    cx.execute("DELETE FROM stock_feed")
    s = status(cx, today, at(8, 30))
    ck("both received the night before -> kal raat ho gaya", s["night_before"] and s["rows"][0]["night_before"])
    cx.execute("UPDATE mi_file SET received_at='2026-09-15T09:07:30+05:30' WHERE md5='b'")
    cx.execute("UPDATE mi_file SET received_at='2026-09-15T09:12:00+05:30' WHERE md5='c'")
    # the owner's lists
    cx.execute("INSERT INTO mi_file (md5,type,date_from,date_to,verdict,received_at) VALUES ('s0','SALT_WISE_ITEM_LIST','2026-09-10','2026-09-10','VERIFIED','2026-09-10T20:25:00+05:30')")
    cx.execute("INSERT INTO mi_file (md5,type,date_from,date_to,verdict,received_at) VALUES ('i0','ITEM_MASTER','2026-08-28','2026-08-28','VERIFIED','2026-08-28T10:00:00+05:30')")
    s = status(cx, today, at(10, 30))
    L = {l["key"]: l for l in s["owner_lists"]}
    ck("salt list 5 days old is not overdue; item list 18 days is not; the category list, never seen, is",
       not L["SALT_WISE_ITEM_LIST"]["overdue"] and L["SALT_WISE_ITEM_LIST"]["age_days"] == 5
       and not L["ITEM_MASTER"]["overdue"] and L["CATEGORY_WISE_ITEM_LIST"]["overdue"] and s["overdue"] == ["CATEGORY_WISE_ITEM_LIST"])
    s36 = status(cx, date(2026, 10, 3), datetime(2026, 10, 3, 9, tzinfo=IST))
    L = {l["key"]: l for l in s36["owner_lists"]}
    ck("on 03-Oct the item list is 36 days old -> overdue; the salt list 23 days -> overdue",
       L["ITEM_MASTER"]["overdue"] and L["SALT_WISE_ITEM_LIST"]["overdue"] and "item list 36 days" in s36["line"])
    # the 1st of the month
    ck("on the 3rd the two monthly rows are on the page, due, as on 30-09",
       [r["key"] for r in s36["rows"][2:4]] == ["STOCK_VALUATION", "STOCK_EXPIRY"] and s36["rows"][2]["state"] == "due"
       and "30-09-2026" in s36["rows"][2]["hint"])
    cx.execute("INSERT INTO mi_file (md5,type,date_from,date_to,verdict,received_at) VALUES ('v1','STOCK_VALUATION','2026-09-30','2026-09-30','VERIFIED','2026-10-01T08:00:00+05:30')")
    s36 = status(cx, date(2026, 10, 3), datetime(2026, 10, 3, 9, tzinfo=IST))
    ck("a valuation as on 30-09 received on the 1st -> tick, structural, and it says so",
       s36["rows"][2]["state"] == "ok" and s36["rows"][2]["cert"] == "structural" and "spine" in s36["rows"][2]["note"])
    ck("on the 9th the monthly rows are gone", all(not r.get("monthly") for r in status(cx, date(2026, 10, 9), datetime(2026, 10, 9, 9, tzinfo=IST))["rows"]))
    # Amir's day, as before
    cx.execute("INSERT INTO amir_day (day, opened_at) VALUES (?, ?)", (today.isoformat(), "x"))
    s = status(cx, today, at(10, 30))
    ck("Amir day -> the purchase pair appears, due", s["amir_day"] and s["total"] == 4
       and [r["key"] for r in s["rows"][2:4]] == ["PURCHASE_ITEMWISE", "PURCHASE_BILLWISE"] and s["rows"][2]["state"] == "due")
    cx.execute("INSERT INTO purchase_export VALUES ('p1','BILLWISE','f','2026-09-01','2026-09-14','20260915-093000','2026-09-15T09:30:10',3,0,NULL)")
    cx.execute("INSERT INTO purchase_export VALUES ('p2','ITEMWISE','f','2026-09-01','2026-09-10','20260915-093100','2026-09-15T09:31:10',3,0,NULL)")
    s = status(cx, today, at(10, 30))
    ck("bill-wise to yesterday arrives (structural tick); item-wise that stops at the 10th does not",
       s["rows"][3]["state"] == "ok" and s["rows"][3]["cert"] == "structural" and s["rows"][2]["state"] == "due")
    cx.execute("INSERT INTO purchase_export VALUES ('p3','ITEMWISE','f','2026-09-01','2026-09-15','20260914-093100','2026-09-15T09:41:10',3,0,NULL)")
    s = status(cx, today, at(10, 30))
    ck("received today counts even with an older stamp", s["rows"][2]["state"] == "ok")
    cx.execute("INSERT INTO purchase_salt_task (section,seq,a,b,done,done_at) VALUES ('rename',1,'A','B',1,'2026-09-14 18:00:00')")
    s = status(cx, today, at(10, 30))
    ck("a salt tick newer than the last list -> the salt row appears, due", s["total"] == 5 and s["rows"][4]["key"] == "SALT_WISE_ITEM_LIST"
       and s["rows"][4]["state"] == "due")
    cx.execute("INSERT INTO mi_file (md5,type,date_from,date_to,verdict,received_at) VALUES ('s1','SALT_WISE_ITEM_LIST','2026-09-15','2026-09-15','VERIFIED','2026-09-15T09:50:00+05:30')")
    s = status(cx, today, at(10, 30))
    ck("the list arrives after the tick -> arrived, awaiting the reader", s["rows"][4]["state"] == "arrived" and s["all_in"] and not s["all_certified"])
    reading("s1", "SALT_WISE_ITEM_LIST", True, n_items=374)
    s = status(cx, today, at(10, 30))
    ck("the spine reads it -> tick, 374 items, and the whole page is certified", s["rows"][4]["state"] == "ok"
       and s["rows"][4]["count"] == "374 items" and s["all_certified"])
    ck("owner's line 5 of 5, no OVERDUE for the salt list any more, category list still overdue",
       s["line"].startswith("Today's reports: 5 of 5 arrived") and "salt list" not in s["line"] and "category list never" in s["line"])
    s2 = status(cx, date(2026, 9, 16), datetime(2026, 9, 16, 9, tzinfo=IST))
    ck("next day: the tick is older than the list and no list today -> no salt row", all(r["key"] != "SALT_WISE_ITEM_LIST" for r in s2["rows"]))
    ck("timestamps normalise", _norm_ts("20260913-091233") == "2026-09-13 09:12:33" and _hhmm("2026-09-13T09:12:33+05:30") == "09:12")
    ck("Hindi reasons cover the router's words", "pehchan" in hindi_reason("no signature matches this title: 'X'", "UNKNOWN")
       and "Item detail" in hindi_reason("this export carries NO item detail") and "band karke" in hindi_reason("the bytes are not really a .xls file"))
    ck("Hindi reasons cover the reader's witness names", "total" in hindi_failed(["TOTAL units = sum of every line"]).lower()
       and "lines" in hindi_failed(["serial run 1..N unbroken"]).lower() and "tareekh" in hindi_failed(["the report names its date"]))
    # the page renders every state without a template error
    h = render(s)
    ck("the page renders: title, the tick line, the owner never sees a number of a person",
       "Aaj ki reports" in h and "jaanch poori" in h and "Aaj ka kaam poora" in h)
    h2 = render(status(cx, date(2026, 9, 22), datetime(2026, 9, 22, 11, tzinfo=IST)))
    ck("a missed morning renders the red banner and the how-to block with the due date",
       "banner missed" in h2 and "BILL WISE STATEMENT" in h2 and "21-09-2026" in h2)
    # a reading the spine does not use certifies nothing
    reading("z", None, None)
    ck("a reading with no family is no certificate", certify("z", "", "SALE_BILLWISE") is None)
    ck("a type the spine has no reader for is never certified from the store", certify("b", "", "STOCK_VALUATION") is None)
    print("reports_tile selftest: %d checks, %d failures" % (n_checks[0], len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(selftest())
