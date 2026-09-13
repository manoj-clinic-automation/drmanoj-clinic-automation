"""
reports_tile.py -- "Aaj ki reports": the Marg report generator's morning page.  (S243, 13-Sep-2026)

THE OWNER'S RULING, 13-Sep-2026.  Shavez (portal login `shavez`, role manager) becomes the Marg
REPORT GENERATOR -- a morning job on the medical PC, before any sale starts, and on Amir's days
too -- so that this job leaves the owner's desk.  He needs a staff-friendly page: he generates
the reports in Marg; the server sees each one arrive through the one door (marg_take.take ->
mi_file, the pushed-report staging, the purchase push, the stock snapshot) within seconds; his
page confirms each, and prompts him ONLY for the refused and the still-due ones.

PRINCIPLES (the same as Amir's page, D469):
  * He is never asked whether a report arrived.  The server reads what it already holds and
    TELLS him.  Nothing on this page writes anything.
  * The medical PC comes up 8-10:30, so nothing is "late" by the clock.  A row is simply DUE
    until it arrives (○ baaki), ARRIVED when a verified copy is here (✓ aa gayi, with the time),
    or REFUSED when the newest copy the server saw was not accepted (✗ manzoor nahi, with the
    reason in plain Hindi).  A verified copy always wins over an earlier refusal.
  * One instruction line only: "Marg me report banao, yahan khud tick ho jayegi".
  * No JavaScript frameworks; no JavaScript at all.  Server-rendered HTML, phone first,
    Hinglish in Latin script (as Amir's steps).  The page refreshes itself every 30 s
    (meta refresh), so a report he has just generated ticks itself while the phone lies on
    the desk.

WHAT IS DUE TODAY (the rows):
  1  SALE_BILLWISE for YESTERDAY      mi_file type SALE_BILLWISE, verdict VERIFIED, date range
                                       covering yesterday; or a marg_push_staging row (not
                                       'rejected') whose survey names yesterday.
  2  STOCK_CLOSING as on yesterday's  mi_file STOCK_CLOSING VERIFIED with as-on (date_from)
     close                             yesterday -- or today (a morning closing before sales is
                                       yesterday's close, export_watch's rule); or stock_feed
                                       source push_snapshot with as_on yesterday/today.
  3  on AMIR DAYS only                PURCHASE item lines (purchase_export ITEMWISE /
     (Amir punched today on the        BILLITEMWISE, or mi_file PURCHASE_ITEMWISE /
     biometric machine -- export_       PURCHASE_BILLITEMWISE VERIFIED) and PURCHASE_BILLWISE
     watch's punch logic, machine id    (purchase_export BILLWISE, or mi_file PURCHASE_BILLWISE
     from the staff register, 101 as    VERIFIED), each received TODAY and covering the 1st of
     the fallback -- or an amir_day     the month to yesterday (on the 1st: today).
     row for today)
  4  SALT_WISE_ITEM_LIST              only when the salt refresh is due: purchase_salt_task has a
                                       tick (done_at) newer than the last VERIFIED SALT_WISE
                                       arrival in mi_file -- or one arrived today (then it shows
                                       as arrived).  Otherwise the row is not shown at all.

THE OWNER sees the same status as ONE English line on the hub's Marg card:
    "Today's reports: 2 of 3 arrived"   (from /finance/reports/aaj/api/status)

GATE: any role on the medical unit (maker / checker / viewer), exactly as Amir's page: the unit
has one maker, one checker and a few viewers, and the person doing this job holds `viewer` at
least (seed_reports_role_s243.py gives `shavez` that row if he has none).  Anonymous is sent to
the portal by finance_app's own before_request gate before this module is reached.

Nothing here writes to the database.  No table is created.  Every read is guarded against a
table that does not exist yet (the purchase, stock and marg_ingest tables are lazy, F-303).
"""

import csv
import html
import io
import os
import sqlite3
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

KIT = "S243_REPORTS_TILE"

# purchase_export types that carry the item lines (either grouping counts, export_watch's rule)
PURCHASE_LINE_TYPES = ("ITEMWISE", "BILLITEMWISE")
MI_PURCHASE_LINE_TYPES = ("PURCHASE_ITEMWISE", "PURCHASE_BILLITEMWISE")


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------

def _now():
    return datetime.now(IST)


def _today():
    return _now().date()


def _esc(v):
    return html.escape("" if v is None else str(v))


def _table_exists(cx, name):
    r = cx.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone()
    return r is not None


def _norm_ts(s):
    """Any timestamp this box writes -> 'YYYY-MM-DD HH:MM:SS' so strings compare as time.
    Shapes seen: '2026-09-13T09:12:33+05:30' (marg_take), '2026-09-13T09:12:33' (now_iso),
    '2026-09-13 09:12:33' (amir_salts), '20260913-091233' (a Marg export stamp)."""
    if not s:
        return ""
    s = str(s).strip()
    if len(s) == 15 and s[8] == "-" and s[:8].isdigit() and s[9:].isdigit():
        return "%s-%s-%s %s:%s:%s" % (s[0:4], s[4:6], s[6:8], s[9:11], s[11:13], s[13:15])
    s = s.replace("T", " ")
    return s[:19]


def _hhmm(s):
    n = _norm_ts(s)
    return n[11:16] if len(n) >= 16 else n


def _ddmm(d):
    """A date for a Hindi-first reader: 12-09-2026."""
    if isinstance(d, str):
        try:
            d = date.fromisoformat(d[:10])
        except ValueError:
            return d
    return d.strftime("%d-%m-%Y")


def _day_word(d):
    return ("Somvaar", "Mangalvaar", "Budhvaar", "Guruvaar", "Shukravaar", "Shanivaar", "Ravivaar")[d.weekday()]


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


# --------------------------------------------------------------------------
# what the server already holds
# --------------------------------------------------------------------------

def _mi_rows(cx, types, day_from=None, day_to=None, received_day=None):
    """mi_file rows of the given types (the marg_ingest / marg_take door).  Pure read."""
    if not _table_exists(cx, "mi_file"):
        return []
    q = ("SELECT md5, type, verdict, reason, pc_verdict, date_from, date_to, received_at, stamp, drive_name "
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


def _pick(ok_rows, bad_rows):
    """The state of one row: a verified copy wins; else the newest refusal; else due."""
    if ok_rows:
        best = max(ok_rows, key=lambda r: _norm_ts(r.get("received_at")))
        return {"state": "ok", "at": _hhmm(best.get("received_at")), "when": _norm_ts(best.get("received_at"))}
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
            ok.append({"received_at": r["received_at"]})
    bad = [r for r in _mi_rows(cx, ("SALE_BILLWISE",), received_day=today_iso) if r["verdict"] != "VERIFIED"]
    if not bad:
        bad = [r for r in _mi_rows(cx, ("SALE_BILLWISE",), day_from=y_iso, day_to=y_iso) if r["verdict"] != "VERIFIED"]
    if not bad and _table_exists(cx, "marg_push_staging"):
        for r in cx.execute("SELECT received_at, survey_json, filename_hint FROM marg_push_staging "
                            "WHERE status='rejected' AND substr(received_at,1,10)=? "
                            "ORDER BY received_at DESC LIMIT 1", (today_iso,)).fetchall():
            why = ""
            try:
                import json
                why = (json.loads(r["survey_json"] or "{}") or {}).get("error") or ""
            except Exception:                                  # noqa: BLE001
                why = ""
            bad.append({"received_at": r["received_at"], "verdict": "REFUSED", "reason": why, "pc_verdict": ""})
    st = _pick(ok, bad)
    st.update(key="SALE_BILLWISE", label="Bill-wise sale report",
              hint="kal ki, %s" % _ddmm(y_iso))
    return st


def _stock_row(cx, y_iso, today_iso):
    # Marg's "as on" is date_from.  Yesterday's close = as on yesterday, or as on this morning
    # (a closing taken before the counter opens); both count, as export_watch already rules.
    ok = [r for r in _mi_rows(cx, ("STOCK_CLOSING",))
          if r["verdict"] == "VERIFIED" and (r.get("date_from") or "")[:10] in (y_iso, today_iso)
          and (r.get("received_at") or "")[:10] >= y_iso]
    if _table_exists(cx, "stock_feed"):
        for as_on in (date.fromisoformat(y_iso).strftime("%d-%m-%Y"), date.fromisoformat(today_iso).strftime("%d-%m-%Y")):
            r = cx.execute("SELECT MIN(received_at) AS at, COUNT(*) AS n FROM stock_feed WHERE as_on=? "
                           "AND source LIKE 'push_snapshot%'", (as_on,)).fetchone()
            if r and r["n"] and (r["at"] or "")[:10] >= y_iso:
                ok.append({"received_at": r["at"]})
    bad = [r for r in _mi_rows(cx, ("STOCK_CLOSING",), received_day=today_iso) if r["verdict"] != "VERIFIED"]
    st = _pick(ok, bad)
    st.update(key="STOCK_CLOSING", label="Stock closing report",
              hint="kal shaam tak ka stock (as on %s)" % _ddmm(y_iso))
    return st


def _purchase_rows(cx, y_iso, today_iso):
    """The daily pair, month-to-date, received today.  export_watch's coverage rule."""
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
    st = _pick(pe(PURCHASE_LINE_TYPES) + ok_mi, bad_mi)
    st.update(key="PURCHASE_ITEMWISE", label="Purchase item-wise report",
              hint="1 tareekh se aaj tak (Amir ke din)")
    out.append(st)
    ok_mi, bad_mi = mi(("PURCHASE_BILLWISE",))
    st = _pick(pe(("BILLWISE",)) + ok_mi, bad_mi)
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
    st = _pick(ok, bad)
    st.update(key="SALT_WISE_ITEM_LIST", label="Salt-wise item list",
              hint="salt ka kaam hua hai -- nayi list chahiye" if due else "aaj aayi")
    return st


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
# the day, gathered once
# --------------------------------------------------------------------------

def status(cx, today=None):
    today = today or _today()
    today_iso = today.isoformat()
    y_iso = (today - timedelta(days=1)).isoformat()
    amir, amir_why = _amir_day(cx, today)
    rows = [_sale_row(cx, y_iso, today_iso), _stock_row(cx, y_iso, today_iso)]
    if amir:
        rows += _purchase_rows(cx, y_iso, today_iso)
    salt = _salt_row(cx, today_iso)
    if salt:
        rows.append(salt)
    # files the server could not place at all today (no type): said once, at the end
    unknown = [r for r in _mi_refusals_today(cx, today_iso)
               if (r.get("type") or "") in ("", "_UNKNOWN", "UNKNOWN")]
    arrived = sum(1 for r in rows if r["state"] == "ok")
    refused = sum(1 for r in rows if r["state"] == "refused")
    total = len(rows)
    line = "Today's reports: %d of %d arrived" % (arrived, total)
    if refused:
        line += ", %d refused" % refused
    return {"ok": True, "kit": KIT, "day": today_iso, "yesterday": y_iso, "amir_day": amir, "amir_why": amir_why,
            "rows": rows, "arrived": arrived, "refused": refused, "total": total, "all_in": arrived == total,
            "unknown_today": [{"at": _hhmm(u.get("received_at")), "reason": u.get("reason") or "",
                               "reason_hi": hindi_reason(u.get("reason"), u.get("verdict"))} for u in unknown[:3]],
            "line": line, "at": _now().strftime("%Y-%m-%d %H:%M:%S")}


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
.small{color:var(--soft);font-size:13px}
.state{display:block;margin-top:2px;font-size:16px}
.why{display:block;margin-top:6px;padding:10px;background:#fff8e1;border:1px solid #f0e0a8;border-radius:8px}
.done{background:#e7f3e9;border-color:#bfe0c6}
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
    if r["state"] == "ok":
        state = ("<span class='state good'>&#10003; aa gayi <span class=small>%s baje</span></span>"
                 % _esc(r.get("at", "")))
    elif r["state"] == "refused":
        state = ("<span class='state bad'>&#10007; manzoor nahi <span class=small>%s baje</span></span>"
                 "<span class=why>%s<br><span class=small>%s</span></span>"
                 % (_esc(r.get("at", "")), _esc(r.get("reason_hi", "")), _esc(r.get("reason", ""))))
    else:
        state = "<span class='state due'>&#9675; baaki</span>"
    return ("<div class=line><span class=big>%s</span> <span class=small>%s</span>%s</div>"
            % (_esc(r["label"]), _esc(r.get("hint", "")), state))


def render(s, picked_date=False):
    d = date.fromisoformat(s["day"])
    head = ("<h1>Aaj ki reports</h1><p class=sub>%s, %s%s</p>"
            % (_day_word(d), _ddmm(d), " &middot; Amir ka din" if s["amir_day"] else ""))
    lead = "<p class=big>Marg me report banao, yahan khud tick ho jayegi.</p>"
    rows = "".join(_row_html(r) for r in s["rows"])
    body = head + lead + "<div class=card>" + rows + "</div>"
    if s["unknown_today"]:
        u = s["unknown_today"][0]
        body += ("<div class='card'><div class=line><span class='big bad'>&#10007; Ek file pehchan nahi aayi "
                 "<span class=small>%s baje</span></span><span class=why>%s<br><span class=small>%s</span></span>"
                 "</div></div>" % (_esc(u["at"]), _esc(u["reason_hi"]), _esc(u["reason"])))
    if s["all_in"] and s["total"]:
        body += "<div class='card done'><p class='big good' style='margin:0'>&#10003; Aaj ki sab reports aa gayi.</p></div>"
    else:
        body += ("<p class=foot>%d / %d aa gayi</p>" % (s["arrived"], s["total"]))
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
# selftest -- the arithmetic on an in-memory db, no Flask
# --------------------------------------------------------------------------

def selftest():
    fails = []
    n_checks = [0]

    def ck(n, c):
        n_checks[0] += 1
        print(("  ok   " if c else "  FAIL ") + n)
        if not c:
            fails.append(n)
    cx = sqlite3.connect(":memory:")
    cx.row_factory = sqlite3.Row
    today = date(2026, 9, 13)
    y = "2026-09-12"
    s = status(cx, today)
    ck("empty db: two rows, both due, nothing crashes", s["total"] == 2 and all(r["state"] == "due" for r in s["rows"]))
    ck("owner's line reads 0 of 2", s["line"] == "Today's reports: 0 of 2 arrived")
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
               (y, y, "2026-09-13T09:01:00+05:30"))
    s = status(cx, today)
    ck("a refused sale report shows refused with a Hindi reason",
       s["rows"][0]["state"] == "refused" and "Excel" in s["rows"][0]["reason_hi"] and s["rows"][0]["at"] == "09:01")
    cx.execute("INSERT INTO mi_file (md5,type,date_from,date_to,verdict,received_at) VALUES ('b','SALE_BILLWISE',?,?,'VERIFIED',?)",
               (y, y, "2026-09-13T09:07:30+05:30"))
    s = status(cx, today)
    ck("a later verified copy wins: aa gayi 09:07", s["rows"][0]["state"] == "ok" and s["rows"][0]["at"] == "09:07")
    cx.execute("INSERT INTO stock_feed (as_on,source,item,qty,received_at) VALUES ('13-09-2026','push_snapshot','X',1,'2026-09-13T09:09:00')")
    s = status(cx, today)
    ck("a morning stock snapshot as on today counts as yesterday's close", s["rows"][1]["state"] == "ok")
    ck("no Amir row, no salt row yet", s["total"] == 2 and s["all_in"])
    cx.execute("INSERT INTO amir_day (day, opened_at) VALUES (?, ?)", (today.isoformat(), "x"))
    s = status(cx, today)
    ck("Amir day -> the purchase pair appears, due", s["amir_day"] and s["total"] == 4
       and [r["key"] for r in s["rows"][2:4]] == ["PURCHASE_ITEMWISE", "PURCHASE_BILLWISE"] and s["rows"][2]["state"] == "due")
    cx.execute("INSERT INTO purchase_export VALUES ('p1','BILLWISE','f','2026-09-01','2026-09-12','20260913-093000','2026-09-13T09:30:10',3,0,NULL)")
    cx.execute("INSERT INTO purchase_export VALUES ('p2','ITEMWISE','f','2026-09-01','2026-09-10','20260913-093100','2026-09-13T09:31:10',3,0,NULL)")
    s = status(cx, today)
    ck("bill-wise to yesterday arrives; item-wise that stops at the 10th does not",
       s["rows"][3]["state"] == "ok" and s["rows"][2]["state"] == "due")
    cx.execute("INSERT INTO purchase_export VALUES ('p3','ITEMWISE','f','2026-09-01','2026-09-13','20260912-093100','2026-09-13T09:41:10',3,0,NULL)")
    s = status(cx, today)
    ck("received today counts even with an older stamp", s["rows"][2]["state"] == "ok")
    cx.execute("INSERT INTO purchase_salt_task (section,seq,a,b,done,done_at) VALUES ('rename',1,'A','B',1,'2026-09-12 18:00:00')")
    s = status(cx, today)
    ck("a salt tick with no list ever -> the salt row appears, due", s["total"] == 5 and s["rows"][4]["key"] == "SALT_WISE_ITEM_LIST"
       and s["rows"][4]["state"] == "due")
    cx.execute("INSERT INTO mi_file (md5,type,date_from,date_to,verdict,received_at) VALUES ('s1','SALT_WISE_ITEM_LIST','2026-09-13','2026-09-13','VERIFIED','2026-09-13T09:50:00+05:30')")
    s = status(cx, today)
    ck("the list arrives after the tick -> aa gayi", s["rows"][4]["state"] == "ok" and s["all_in"])
    ck("owner's line 5 of 5", s["line"] == "Today's reports: 5 of 5 arrived")
    s2 = status(cx, date(2026, 9, 14))
    ck("next day: the tick is older than the list and no list today -> no salt row", all(r["key"] != "SALT_WISE_ITEM_LIST" for r in s2["rows"]))
    ck("timestamps normalise", _norm_ts("20260913-091233") == "2026-09-13 09:12:33" and _hhmm("2026-09-13T09:12:33+05:30") == "09:12")
    ck("Hindi reasons cover the router's words", "pehchan" in hindi_reason("no signature matches this title: 'X'", "UNKNOWN")
       and "Item detail" in hindi_reason("this export carries NO item detail") and "band karke" in hindi_reason("the bytes are not really a .xls file"))
    print("reports_tile selftest: %d checks, %d failures" % (n_checks[0], len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    import sys
    sys.exit(selftest())
