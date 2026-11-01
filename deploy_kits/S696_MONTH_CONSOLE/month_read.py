#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""month_read.py -- S696_MONTH_CONSOLE (the parent; session 376, 01-Nov-2026). THE MONTH, as one reading.

The owner's words (01-Nov, 13:41-17:59 IST, on the mock-up https://claude.ai/artifact/B4u8r6vLHwjywWr9NQjhaW): one page on his
command console that shows, for the month just ended and for the running month, where the month stands -- the seven groups of
month-end work in calendar order with his own actions on them -- then the revenue by head with a subtotal under each head and
the grand total, the X-ray expenses against the X-ray revenue, what was bought for the rooms, and the supplies and replacements.

ONE READING LAYER, like owner_console.py: nothing here writes, nothing here makes a figure of its own. Every line is the answer
of the module that owns it (packs, purchase_app, sanjeevni_cash, returns_kinds, month_jobs, xray_film, clinic_lists, the staff
register's tables, petty_book's tables, the physio tables) or one plain SELECT on a table the owner's pages already show.
It runs ONLY inside owner_console.py --build, on the COPY of finance.db that the builder makes, with FINANCE_DB pointed at the
copy before any module of the app is imported. The staff register's database and the Scan App's database are opened read-only
(mode=ro). A piece that cannot be read is said on the page ("not read: ..."), never silently missing (the console's own rule).

NO PATIENT IN THE READING: counts, codes and amounts only. No name, clinic ID, phone or slip number leaves this module.

read(con, env, now) -> {"ok": True, "months": [<the month before now>, <the running month>], "built": "...", "version": ...}
Each month: ym, label, state ('ended' | 'running'), summary, groups (7), revenue, xray, bought, supplies, unread.
"""
import datetime as dt
import os
import sqlite3

VERSION = "S696 1.1"
BASE_URL = ""                        # paths are site-relative; the page is served from the same host

# the pages a line opens (the owner's, as they stand at S696)
P = dict(
    attcorr="/register/attcorr?ym=%s", salary="/register/salary?ym=%s", flow="/register/salary/flow?ym=%s",
    approvals="/finance/approvals", pmonth="/finance/purchase/page/month/%s", ppay="/finance/purchase/page/pay/%s",
    pcheq="/finance/purchase/page/cheques/%s", dkal="/finance/darpan/kal/month", amir="/finance/amir",
    mj="/finance/monthjobs/owner", aaj="/finance/aaj?as=%s",
    lists="/finance/slips/lists", lists_x="/finance/slips/lists/xray", film="/finance/slips/film/log",
    rate="/finance/clinic/sheets?kind=xray", petty="/finance/petty", renew="/scanapp/renewals",
    packs="/finance/packs", checklist="/finance/packs/checklist?month=%s", papers="/scanapp/papers",
    surgery="/finance/surgery", implants="/finance/surgery/implants", surg_set="/finance/surgery/settings",
    clinic_day="/finance/clinic/day", money="/finance/clinic/money", physio="/finance/physio",
    xcost="/scanapp/xray", station="/scanapp/stationery", batt="/scanapp/batteries", machines="/scanapp/machines",
)
MON = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
FULL = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")
MODE = {"cash": "cash", "online payment": "upi", "upi": "upi", "debit card": "card", "credit card": "card", "card": "card",
        "split payment": "two", "wallet": "upi"}          # his rulings: never the words "split payment"; Wallet = Razorpay to the bank
SIZES = ("8x10", "11x14")
SIZE_LABEL = {"8x10": "8×10", "11x14": "11×14"}
FILMS_PER_BOX = 150


# ============================================================================================ small things
def _first(ym):
    return dt.date(int(ym[:4]), int(ym[5:7]), 1)


def _last(ym):
    f = _first(ym)
    return (dt.date(f.year + 1, 1, 1) if f.month == 12 else dt.date(f.year, f.month + 1, 1)) - dt.timedelta(days=1)


def _prev(ym):
    f = _first(ym)
    return (dt.date(f.year - 1, 12, 1) if f.month == 1 else dt.date(f.year, f.month - 1, 1)).strftime("%Y-%m")


def _next(ym):
    return (_last(ym) + dt.timedelta(days=1)).strftime("%Y-%m")


def mname(ym):
    return "%s %s" % (FULL[int(ym[5:7]) - 1], ym[:4])


def dm(iso):
    try:
        d = dt.date.fromisoformat(str(iso)[:10])
        return "%d %s" % (d.day, MON[d.month - 1])
    except (TypeError, ValueError):
        return str(iso or "")


def when(ts):
    """'1 Nov, 12:40' from an ISO stamp (local), or ''."""
    s = str(ts or "")
    if len(s) < 16:
        return dm(s) if s else ""
    return "%s, %s" % (dm(s), s[11:16])


def _q(con, sql, params=()):
    """One query on the builder's connection with sqlite3.Row rows, whatever row factory the caller set."""
    c = con.cursor()
    c.row_factory = sqlite3.Row
    return c.execute(sql, params)


def _has(con, table):
    try:
        return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None
    except sqlite3.Error:
        return False


def _ro(path, timeout=5):
    c = sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=timeout)
    c.row_factory = sqlite3.Row
    return c


def row(dot, text, href=None, who=None, who_href=None, act=None, act_href=None, act_cls="", links=None, yours=False):
    return dict(dot=dot, text=text, href=href, who=who or "", who_href=who_href, act=act, act_href=act_href, act_cls=act_cls,
                links=links or [], yours=bool(yours or act))


def unread(what, e):
    return row("n", "%s: not read" % what, who="%s: %s" % (type(e).__name__, str(e)[:100]))


def piece(out, what, fn, unread_list):
    """Run one reader; a fault becomes one grey line and one note, never a missing section (the console's own rule)."""
    try:
        r = fn()
        if r is None:
            return
        if isinstance(r, list):
            out.extend(r)
        else:
            out.append(r)
    except Exception as e:                                             # noqa: BLE001
        out.append(unread(what, e))
        unread_list.append("%s: %s: %s" % (what, type(e).__name__, str(e)[:120]))


def group(key, no, title, href, rows, act=None, act_href=None, act_cls="", sub=None, extra=None):
    done = sum(1 for r in rows if r["dot"] == "g")
    yours = sum(1 for r in rows if r["dot"] == "w")
    g = dict(key=key, no=no, title=title, href=href, rows=rows, n=len(rows), done=done, yours=yours,
             waiting=sum(1 for r in rows if r["dot"] == "n"), act=act, act_href=act_href, act_cls=act_cls, sub=sub or [])
    if extra:
        g.update(extra)
    return g


def _sub_from_rows(rows):
    """The closed bar's summary: the first amber row's words, then the first grey one."""
    out = []
    for r in rows:
        if r["dot"] == "w":
            out.append(dict(t=r["text"], href=r.get("act_href") or r.get("href"), y=True))
            break
    for r in rows:
        if r["dot"] == "n" and not out:
            out.append(dict(t=r["text"], href=r.get("href"), y=False))
            break
    return out


# ============================================================================================ 1 · attendance -> salary
def g_attendance(con, env, ym, today, state, un):
    rows = []
    reg = env.get("register")

    def read():
        if not reg or not os.path.exists(reg):
            raise FileNotFoundError("the staff register's database is not here")
        rc = _ro(reg)
        try:
            m = None
            if _has(rc, "attcorr_month"):
                m = rc.execute("SELECT entered_by, entered_ts, checked_by, checked_ts, approved_by, approved_ts FROM attcorr_month WHERE ym=?",
                               (ym,)).fetchone()
            pend = 0
            if _has(rc, "attcorr_day"):
                pend = rc.execute("SELECT COUNT(*) FROM attcorr_day WHERE ym=? AND COALESCE(mark,'')<>COALESCE(applied_mark,'')", (ym,)).fetchone()[0]
            lk = rc.execute("SELECT status, locked_by, locked_ts FROM locked_run WHERE ym=?", (ym,)).fetchone() if _has(rc, "locked_run") else None
        finally:
            rc.close()
        out = []
        ac, sal = P["attcorr"] % ym, P["salary"] % ym
        if state == "running":
            out.append(row("n", "Attendance corrections for %s" % mname(ym), href=ac, who="reception enters them on 1 %s" % MON[_first(_next(ym)).month - 1]))
            out.append(row("n", "Lock the %s salary" % FULL[int(ym[5:7]) - 1], href=sal, who="after the corrections are approved"))
            return out
        if m and m["entered_ts"]:
            out.append(row("g", "Attendance corrections entered", href=ac, who="%s · %s" % (m["entered_by"] or "reception", when(m["entered_ts"]))))
        else:
            out.append(row("n", "Attendance corrections not entered yet", href=ac, who="reception's job on the 1st", who_href=P["aaj"] % "shivani"))
        if m and m["checked_ts"]:
            out.append(row("g", "Checked by %s" % (m["checked_by"] or "Shavez"), href=ac, who=when(m["checked_ts"]), who_href=P["aaj"] % "shavez"))
        elif m and m["entered_ts"]:
            out.append(row("n", "Shavez has not checked yet", href=ac, who="waiting on Shavez", who_href=P["aaj"] % "shavez"))
        if m and m["approved_ts"] and not pend:
            out.append(row("g", "Approved & saved", href=ac, who="%s · %s" % (m["approved_by"] or "manoj", when(m["approved_ts"]))))
        elif m and m["checked_ts"]:
            out.append(row("w", "Approve & save the %s corrections" % FULL[int(ym[5:7]) - 1], href=ac, who="yours · then the salary sheets can be made",
                           act="Approve & save", act_href=ac))
        else:
            out.append(row("n", "Approve & save -- after Shavez's check", href=ac))
        if lk and lk["status"] == "locked":
            out.append(row("g", "%s salary locked" % FULL[int(ym[5:7]) - 1], href=sal, who="%s · %s" % (lk["locked_by"] or "", when(lk["locked_ts"]))))
        elif m and m["approved_ts"]:
            out.append(row("w", "Lock the %s salary · slips" % FULL[int(ym[5:7]) - 1], href=sal, who="yours", act="Lock", act_href=sal,
                           links=[dict(t="Sheet 2", href=P["flow"] % ym)]))
        else:
            out.append(row("n", "Lock the %s salary · slips" % FULL[int(ym[5:7]) - 1], href=sal, who="after the approval",
                           links=[dict(t="Sheet 2", href=P["flow"] % ym)]))
        return out
    piece(rows, "the staff register", read, un)
    act = next((r for r in rows if r["dot"] == "w"), None)
    return group("att", 1, "Attendance → salary", P["flow"] % ym, rows, act=act["act"] if act else None,
                 act_href=act["act_href"] if act else None, sub=_sub_from_rows(rows))


# ============================================================================================ 2 · Sanjeevni
def g_sanjeevni(con, env, ym, today, state, un):
    rows = []
    d0, d1 = _first(ym).isoformat(), min(_last(ym), today).isoformat()

    def days():
        st = {r[0]: r[1] for r in _q(con, "SELECT status, COUNT(*) FROM day_entry WHERE unit='medical' AND business_date BETWEEN ? AND ? GROUP BY status", (d0, d1))}
        n = sum(st.values())
        ap = st.get("approved", 0) + st.get("locked", 0)
        if not n:
            return row("n", "No Sanjeevni day entered yet", href=P["approvals"])
        if ap == n:
            return row("g", "All %d days approved" % n, href=P["approvals"], links=[dict(t="Darpan's month", href=P["dkal"])])
        return row("w", "%d of %d days approved · %d waiting" % (ap, n, n - ap), href=P["approvals"], act="Approve", act_href=P["approvals"])
    piece(rows, "Sanjeevni's days", days, un)

    def purchases():
        import purchase_app as pa                                      # noqa: PLC0415
        ms = pa._month_status(con, ym)
        href = P["pmonth"] % ym
        if ms.get("status") == "final":
            return row("g", "Purchases finalised", href=href, who="%s · %s" % (ms.get("finalised_by") or "", when(ms.get("finalised_at"))))
        if state == "running":
            return row("n", "Finalise the purchases -- after the month-end Marg reports", href=href)
        s = pa._month_summary(con, ym)
        can, reasons = pa._lock_gate(con, ym, s)
        if can:
            return row("w", "Finalise %s purchases" % FULL[int(ym[5:7]) - 1], href=href, who="yours · the gate is open", act="Finalise", act_href=href)
        return row("n", "Finalise the purchases -- the gate is not open", href=href, who=(reasons[0] if reasons else "")[:140],
                   links=[dict(t="Amir", href=P["amir"])])
    piece(rows, "the purchase month", purchases, un)

    def pay():
        href = P["ppay"] % ym
        neft = _has(con, "purchase_neft_event") and _q(con, "SELECT 1 FROM purchase_neft_event WHERE month=? AND kind<>'rejected'", (ym,)).fetchone()
        if neft:
            return row("g", "Vendor payments: NEFT done", href=href, links=[dict(t="cheque register", href=P["pcheq"] % ym)])
        chk = _q(con, "SELECT ok, who, at FROM purchase_pay_check WHERE month=? ORDER BY id DESC LIMIT 1", (ym,)).fetchone() if _has(con, "purchase_pay_check") else None
        if chk and chk["ok"]:
            return row("n", "Vendor payments sheet verified · NEFT advice next", href=href, who="%s · %s" % (chk["who"], when(chk["at"])), who_href=P["aaj"] % "shavez",
                       links=[dict(t="cheque register", href=P["pcheq"] % ym)])
        if state == "running":
            return row("n", "Vendor payments sheet -- after the finalise", href=href)
        return row("n", "Vendor payments sheet not verified yet", href=href, who="Shavez", who_href=P["aaj"] % "shavez",
                   links=[dict(t="cheque register", href=P["pcheq"] % ym)])
    piece(rows, "the vendor payments", pay, un)

    def lock():
        st = {r[0]: r[1] for r in _q(con, "SELECT status, COUNT(*) FROM day_entry WHERE unit='medical' AND business_date BETWEEN ? AND ? GROUP BY status", (d0, d1))}
        n = sum(st.values())
        if n and st.get("locked", 0) == n:
            return row("g", "%s locked" % FULL[int(ym[5:7]) - 1], href=P["approvals"])
        if state == "running":
            return row("n", "%s: Check it → Lock it -- after the month ends" % FULL[int(ym[5:7]) - 1], href=P["approvals"])
        return row("w", "%s: Check it → Lock it" % FULL[int(ym[5:7]) - 1], href=P["approvals"], who="yours", act="Check it", act_href=P["approvals"], act_cls="soft")
    piece(rows, "the Sanjeevni month", lock, un)
    act = next((r for r in rows if r["dot"] == "w" and r.get("act")), None)
    return group("sanj", 2, "Sanjeevni", P["approvals"], rows, act=act["act"] if act else None, act_href=act["act_href"] if act else None,
                 act_cls=act["act_cls"] if act else "", sub=_sub_from_rows(rows))


# ============================================================================================ 3 · Darpan's month jobs
def g_darpan(con, env, ym, today, state, un):
    rows = []

    def read():
        import month_jobs as MJ                                        # noqa: PLC0415
        out = []
        ref = _last(ym) if state == "ended" else today                 # the jobs are judged as on the month's last day, or today
        # expiry clear-out
        try:
            ex = MJ.expiry_state(con, ref)
            if not ex["open"]:
                out.append(row("n", "Expiry clear-out opens %s" % dm(ex.get("next")), href=P["mj"]))
            elif ex["waiting"]:
                out.append(row("n", "Expiry clear-out · %d line%s waiting" % (ex["waiting"], "" if ex["waiting"] == 1 else "s"), href=P["mj"],
                               who="Darpan", who_href=P["aaj"] % "darpan"))
            else:
                out.append(row("g", "Expiry clear-out · %d line%s done" % (len(ex["rows"]), "" if len(ex["rows"]) == 1 else "s"), href=P["mj"]))
        except Exception as e:                                         # noqa: BLE001
            out.append(unread("the expiry clear-out", e))
        # vehicle check
        try:
            vs = MJ.vehicle_state(con, ref)
            if not vs["open"]:
                out.append(row("n", "Vehicle check opens %s" % dm(vs.get("next")), href=P["mj"]))
            elif vs["check"] is None:
                out.append(row("n", "Vehicle check · %d vehicles" % len(vs["vehicles"]), href=P["mj"], who="waiting on Darpan · from %s" % dm(vs["due_from"]),
                               who_href=P["aaj"] % "darpan"))
            else:
                c = vs["check"]
                out.append(row("g", "Vehicle check done", href=P["mj"], who="%s · %s" % (c["saved_by"], when(c["saved_at"]))))
        except Exception as e:                                         # noqa: BLE001
            out.append(unread("the vehicle check", e))
        # home medicines (counted in the last 7 days of a month for the NEXT month)
        try:
            hs = MJ.home_state(con, ref)
            n_items = len(hs["items"])
            if not n_items:
                out.append(row("w", "Home medicines · your list is empty", href=P["mj"], who="yours · name, unit, needed per month", act="Fill the list", act_href=P["mj"], act_cls="soft"))
            elif hs["count"] is not None:
                out.append(row("g", "Home medicines counted for %s" % mname(hs["month"]), href=P["mj"], who="%s · %s" % (hs["count"]["saved_by"], when(hs["count"]["saved_at"]))))
            else:
                out.append(row("n", "Home medicines count · %d item%s" % (n_items, "" if n_items == 1 else "s"), href=P["mj"],
                               who="opens %s" % dm(hs["due_from"])))
        except Exception as e:                                         # noqa: BLE001
            out.append(unread("the home medicines", e))
        # vehicle papers
        try:
            n_dates = _q(con, "SELECT COUNT(*) FROM mj_paper WHERE COALESCE(expiry,'')<>''").fetchone()[0] if _has(con, "mj_paper") else 0
            if not n_dates:
                out.append(row("w", "Vehicle paper dates not typed", href=P["mj"], who="yours · pollution, insurance, RC", act="Type dates", act_href=P["mj"], act_cls="soft"))
            else:
                soon = _q(con, "SELECT COUNT(*), MIN(expiry) FROM mj_paper WHERE COALESCE(expiry,'')<>'' AND expiry <= ?",
                                   ((today + dt.timedelta(days=45)).isoformat(),)).fetchone()
                if soon[0]:
                    out.append(row("w", "%d vehicle paper%s due within 45 days" % (soon[0], "" if soon[0] == 1 else "s"), href=P["mj"], who="first: %s" % dm(soon[1])))
                else:
                    nx = _q(con, "SELECT MIN(expiry) FROM mj_paper WHERE COALESCE(expiry,'')<>'' AND expiry > ?", (today.isoformat(),)).fetchone()[0]
                    out.append(row("g", "Paper reminders · none due · %d dates typed" % n_dates, href=P["mj"], who=("next: %s" % dm(nx)) if nx else ""))
        except Exception as e:                                         # noqa: BLE001
            out.append(unread("the vehicle papers", e))
        return out
    piece(rows, "Darpan's month jobs", read, un)
    act = next((r for r in rows if r["dot"] == "w" and r.get("act")), None)
    return group("darpan", 3, "Darpan's month jobs", P["mj"], rows, act=act["act"] if act else None, act_href=act["act_href"] if act else None,
                 act_cls=act["act_cls"] if act else "", sub=_sub_from_rows(rows), extra=dict(list_href=P["aaj"] % "darpan"))


# ============================================================================================ 4 · rooms, and the lists' figures
def lists_figures(con, ym, today):
    """clinic_lists' own rows for the month: counts, amounts and Paid modes by kind -- NO names leave this function."""
    import clinic_lists as CL                                          # noqa: PLC0415
    d0, d1 = _first(ym), min(_last(ym), today)
    out = {}
    for tab in ("proc", "xray"):
        rows = CL.rows_for(con, tab, d0, d1)
        s = CL.summary(rows, tab)
        modes = {"cash": 0, "upi": 0, "card": 0, "two": 0, "other": 0, "free": 0, "dz": 0}
        for e in rows:
            if e.get("dz"):
                modes["dz"] += e["amount_p"]
                continue
            code, mode, _p = e["pd"]
            if code == "free":
                modes["free"] += e["amount_p"]
            elif code == "ok":
                mw = (mode or "").strip().lower()                      # the lists page's own words: Cash, UPI, Card, Paid (two ways)
                modes[{"cash": "cash", "upi": "upi", "card": "card", "paid (two ways)": "two"}.get(mw, MODE.get(mw, "other"))] += e["amount_p"]
            else:
                modes["other"] += e["amount_p"]
        out[tab] = dict(n=int(s["n"]), amt=int(s["amt"]), unpaid=int(s["unpaid"]), days=int(s["days"]), modes=modes,
                        kinds={str(k): [int(v[0]), int(v[1])] for k, v in (s.get("kinds") or {}).items()},
                        films={str(k): int(v) for k, v in (s.get("films") or {}).items()},
                        dz=[int(s["dz"][0]), int(s["dz"][1])] if s.get("dz") else None, nosize=int(s.get("nosize", 0) or 0))
    return out


def g_rooms(con, env, ym, today, state, un, lf):
    rows = []
    d0, d1 = _first(ym), min(_last(ym), today)

    def lists():
        if not lf:
            raise RuntimeError("the lists page could not be read")
        pr, xr = lf["proc"], lf["xray"]
        unpaid = pr["unpaid"] + xr["unpaid"]
        out = [row("g" if not unpaid else "w", "%d slip line%s do not match Docterz · %d procedures, %d X-rays" % (unpaid, "" if unpaid == 1 else "s", pr["unpaid"], xr["unpaid"])
                   if unpaid else "Every slip line matches Docterz", href=P["lists"], who="each a question for Shavez" if unpaid else "",
                   who_href=P["aaj"] % "shavez" if unpaid else None, act="Read %d" % unpaid if unpaid else None, act_href=P["lists"] if unpaid else None, act_cls="soft")]
        out.append(row("g", "%s · %d procedures · %d X-rays" % ("X-ray & procedures month" if state == "ended" else "X-ray & procedures so far", pr["n"], xr["n"]),
                       href=P["lists"], links=[dict(t="rate page", href=P["rate"])]))
        return out
    piece(rows, "the lists", lists, un)

    def film():
        import xray_film as XF                                         # noqa: PLC0415
        ml = XF.month_log(con, ym, today)
        op = all(XF.opening_set(con, z) for z in SIZES)
        who = [] if op else ["opening spare boxes not set (yours, Settings)"]
        if ml["missed"]:
            who.append("%d morning%s not counted" % (ml["missed"], "" if ml["missed"] == 1 else "s"))
        if ml["gapdays"]:
            who.append("%d day%s with a gap" % (ml["gapdays"], "" if ml["gapdays"] == 1 else "s"))
        dot = "w" if not op else ("n" if ml["missed"] else "g")
        return row(dot, "Film log · %s" % (" · ".join(who) if who else "every morning counted, no gap"), href=P["film"],
                   act="Settings" if not op else None, act_href=P["film"] if not op else None, act_cls="soft")
    piece(rows, "the film log", film, un)
    act = next((r for r in rows if r["dot"] == "w" and r.get("act")), None)
    return group("rooms", 4, "Rooms — X-ray, procedures, films", P["lists"], rows, act=act["act"] if act else None,
                 act_href=act["act_href"] if act else None, act_cls=act["act_cls"] if act else "", sub=_sub_from_rows(rows))


# ============================================================================================ 5 · petty book, renewals
def g_petty(con, env, ym, today, state, un):
    rows = []

    def petty():
        if not _has(con, "petty_payee"):
            raise RuntimeError("no petty book")
        pays = _q(con, "SELECT code, name, default_p FROM petty_payee WHERE head='monthly' AND active=1 ORDER BY sort").fetchall()
        d0, d1 = _first(ym).isoformat(), _last(ym).isoformat()
        paid, due = [], []
        for p in pays:
            r = _q(con, "SELECT SUM(amount_p) FROM petty_entry WHERE party=? AND entry_date BETWEEN ? AND ? AND void_at IS NULL", (p["code"], d0, d1)).fetchone()[0]
            (paid if r else due).append((p["name"], r or p["default_p"] or 0))
        if not pays:
            return row("g", "No monthly payee on the petty book", href=P["petty"])
        if due and state == "ended":
            return row("w", "Monthly payees not paid: %s" % ", ".join(n for n, _a in due), href=P["petty"], who="₹%s" % _inr(sum(a for _n, a in due)))
        if due:
            return row("n", "Monthly payees due this month: %s" % ", ".join(n for n, _a in due), href=P["petty"], who="₹%s" % _inr(sum(a for _n, a in due)))
        return row("g", "Monthly payees paid · %s" % ", ".join("%s ₹%s" % (n, _inr(a)) for n, a in paid), href=P["petty"])
    piece(rows, "the petty book", petty, un)

    def renew():
        a = env.get("assets")
        if not a or not os.path.exists(a):
            raise FileNotFoundError("the Scan App's database is not here")
        ac = _ro(a)
        try:
            if not _has(ac, "expiries"):
                raise RuntimeError("no renewals table")
            cols = {r[1] for r in ac.execute("PRAGMA table_info(expiries)")}
            res = "AND COALESCE(resolved,0)=0" if "resolved" in cols else ""
            # the renewals that fall in the month shown, or are already past and still open
            m0, m1 = _first(ym).isoformat(), _last(ym).isoformat()
            n_in = ac.execute("SELECT COUNT(*) FROM expiries WHERE due_date BETWEEN ? AND ? %s" % res, (m0, m1)).fetchone()[0]
            n_past = ac.execute("SELECT COUNT(*) FROM expiries WHERE due_date < ? %s" % res, (m0,)).fetchone()[0]
            nx = ac.execute("SELECT MIN(due_date) FROM expiries WHERE due_date > ? %s" % res, (m1,)).fetchone()[0]
        finally:
            ac.close()
        if n_past:
            return row("w", "%d renewal%s overdue · %d due in %s" % (n_past, "" if n_past == 1 else "s", n_in, FULL[int(ym[5:7]) - 1]), href=P["renew"])
        if n_in:
            return row("w" if state == "running" else "n", "%d renewal%s due in %s" % (n_in, "" if n_in == 1 else "s", FULL[int(ym[5:7]) - 1]), href=P["renew"])
        return row("g", "No renewal due in %s" % FULL[int(ym[5:7]) - 1], href=P["renew"], who=("next: %s" % dm(nx)) if nx else "")
    piece(rows, "the renewals", renew, un)
    return group("petty", 5, "Petty book and renewals", P["petty"], rows, sub=_sub_from_rows(rows), extra=dict(renew_href=P["renew"]))


# ============================================================================================ 6 · the accountants' pack
def g_pack(con, env, ym, today, state, un):
    rows = []
    cl_href = P["checklist"] % ym

    def read():
        import packs as PK                                             # noqa: PLC0415
        out = []
        if state == "running":
            out.append(row("n", "The %s pack opens on 1 %s · due by the 10th" % (FULL[int(ym[5:7]) - 1], MON[_first(_next(ym)).month - 1]), href=P["packs"]))
            cells = PK.cells(con, ym)
            on = sum(1 for c in cells if c.get("state") != "empty")
            out.append(row("n", "Statements already on the shelf: %d of %d" % (on, len(cells)), href=P["packs"]))
            return out
        cells = PK.cells(con, ym)
        on = sum(1 for c in cells if c.get("state") != "empty")
        if on < len(cells):
            out.append(row("w", "Bank statements on the shelf · %d of %d" % (on, len(cells)), href=P["packs"], who="the rest wait on downloads or passwords -- yours",
                           act="Shelf", act_href=P["packs"], act_cls="soft"))
        else:
            out.append(row("g", "Bank statements on the shelf · %d of %d" % (on, len(cells)), href=P["packs"]))
        items = PK.checklist(con, ym, today)
        done = sum(1 for i in items if i["done"])
        late = sum(1 for i in items if i.get("late"))
        openi = [i["item"] for i in items if not i["done"]][:4]
        out.append(row("g" if done == len(items) else "n", "Shavez's checklist · %d of %d done%s" % (done, len(items), (" · %d late" % late) if late else ""),
                       href=cl_href, who=("open: " + "; ".join(openi)) if openi else "", who_href=P["aaj"] % "shavez"))
        prow, _att = PK.pack_rows(con, ym, light=True)
        ready = sum(1 for r in prow if r["status"] == "ready")
        out.append(row("g" if ready == len(prow) else "n", "Pack items ready · %d of %d" % (ready, len(prow)), href=P["packs"],
                       who="; ".join(r["title"].split(" · ", 1)[-1][:40] for r in prow if r["status"] != "ready")[:160]))
        sent = _q(con, "SELECT sent_at, sent_by FROM pack_send WHERE month=? ORDER BY id DESC LIMIT 1", (ym,)).fetchone() if _has(con, "pack_send") else None
        if sent:
            out.append(row("g", "Pack sent to the accountants", href=P["packs"], who="%s · %s" % (sent["sent_by"], when(sent["sent_at"]))))
        else:
            due = _first(_next(ym)) + dt.timedelta(days=9)
            out.append(row("w" if ready == len(prow) else "n", "Send the %s pack" % FULL[int(ym[5:7]) - 1], href=P["packs"],
                           who="your press only · due %s%s" % (dm(due.isoformat()), " · LATE" if today > due else ""), act="Send", act_href=P["packs"], act_cls="send"))
        return out
    piece(rows, "the packs page", read, un)
    act = next((r for r in rows if r["dot"] == "w" and r.get("act")), None)
    return group("pack", 6, "The accountants' pack", P["packs"], rows, act=act["act"] if act else None, act_href=act["act_href"] if act else None,
                 act_cls=act["act_cls"] if act else "", sub=_sub_from_rows(rows), extra=dict(checklist_href=cl_href))


# ============================================================================================ 7 · IPD monthly statement
def g_ipd(con, env, ym, today, state, un):
    rows = []

    def read():
        n_cases = _q(con, "SELECT COUNT(*) FROM surg_case").fetchone()[0] if _has(con, "surg_case") else 0
        waiting = 0
        if _has(con, "surg_implant_bill"):
            waiting = _q(con, "SELECT COUNT(*) FROM surg_implant_bill WHERE COALESCE(void_at,'')=''").fetchone()[0]
        return [row("n", "The hospital's monthly statement and your share both ways", href=P["surgery"],
                    who="kit 5 waits on the hospital's word on the credit heads", links=[dict(t="your share % (Settings)", href=P["surg_set"])]),
                row("n" if not n_cases else "g", "IPD cases on record · %d · implant bills desk · %d bill%s" % (n_cases, waiting, "" if waiting == 1 else "s"),
                    href=P["implants"])]
    piece(rows, "IPD cases", read, un)
    return group("ipd", 7, "IPD monthly statement", P["surgery"], rows, sub=[dict(t="not built · kit 5 waits on the hospital (Y181)", href=P["surgery"], y=False)])


# ============================================================================================ revenue by head
def _inr(p):
    try:
        n = int(round(abs(int(p)) / 100.0))
    except (TypeError, ValueError):
        return "—"
    s = str(n)
    if len(s) > 3:
        s = s[:-3][::-1]
        s = ",".join(s[i:i + 2] for i in range(0, len(s), 2))[::-1] + "," + str(n)[-3:]
    return ("−" if int(p) < 0 else "") + s


def _zero():
    return dict(cash=0, upi=0, card=0, two=0, total=0)


def _add(a, b):
    for k in a:
        a[k] += int(b.get(k) or 0)
    return a


def revenue(con, env, ym, today, state, un, lf):
    d0, d1 = _first(ym).isoformat(), min(_last(ym), today).isoformat()
    heads, notes = [], []

    def clinic():
        if not _has(con, "clinic_day_revenue"):
            raise RuntimeError("no Docterz day revenue")
        t = _q(con, "SELECT COALESCE(SUM(cons_amount_p),0), COALESCE(SUM(xray_amount_p),0), COALESCE(SUM(proc_amount_p),0), COALESCE(SUM(total_amount_p),0), COUNT(*) "
                        "FROM clinic_day_revenue WHERE business_date BETWEEN ? AND ?", (d0, d1)).fetchone()
        by = {}
        for sec, mode, amt in _q(con, "SELECT section, mode, SUM(amount_p) FROM clinic_day_line WHERE business_date BETWEEN ? AND ? AND amount_p>0 GROUP BY 1,2", (d0, d1)):
            m = MODE.get((mode or "").strip().lower())
            if sec in ("consult", "xray", "proc") and m:
                by.setdefault(sec, _zero())
                by[sec][m] += int(amt or 0)
        rows = []
        unmarked = 0
        for sec, label, tot, href in (("consult", "Consultation", t[0], P["clinic_day"]), ("xray", "X-ray", t[1], P["lists"]), ("proc", "Procedures", t[2], P["lists"])):
            r = by.get(sec, _zero())
            r["total"] = int(tot or 0)
            unmarked += max(0, r["total"] - (r["cash"] + r["upi"] + r["card"] + r["two"]))
            note = ""
            if lf and sec == "xray":
                note = "%d lines · films %s %d, %s %d" % (lf["xray"]["n"], SIZE_LABEL["8x10"], lf["xray"]["films"].get("8x10", 0), SIZE_LABEL["11x14"], lf["xray"]["films"].get("11x14", 0))
            if lf and sec == "proc":
                kk = lf["proc"]["kinds"] or {}
                note = "%d lines · " % lf["proc"]["n"] + " · ".join("%s %d" % (k, v[0]) for k, v in kk.items() if v[0])[:80]
            rows.append(dict(label=label, href=href, note=note, **r))
        other = int(t[3] or 0) - int(t[0] or 0) - int(t[1] or 0) - int(t[2] or 0)
        if other:
            rows.append(dict(label="Other", href=P["clinic_day"], note="Docterz's other heads", cash=0, upi=0, card=0, two=0, total=other))
        sub = _zero()
        for r in rows:
            _add(sub, r)
        if unmarked:
            notes.append("₹%s of the clinic's total carries no payment mode in Docterz's lines." % _inr(unmarked))
        heads.append(dict(key="clinic", title="Clinic — Docterz", href=P["clinic_day"], links=[dict(t="day revenue", href=P["clinic_day"]), dict(t="flags", href=P["money"])],
                          rows=rows, sub=dict(label="Clinic subtotal", **sub), days=int(t[4] or 0)))
    piece_h(clinic, "the clinic's revenue", heads, un)

    def sanj():
        import sanjeevni_cash as SC                                    # noqa: PLC0415
        m = next((x for x in SC.month_rows(con, "medical") if x["ym"] == ym), None)
        if not m:
            heads.append(dict(key="sanj", title="Sanjeevni — counter", href=P["approvals"], links=[dict(t="approvals", href=P["approvals"])], rows=[],
                              sub=dict(label="Sanjeevni subtotal", **_zero()), days=0, empty="no Sanjeevni day entered yet"))
            return
        rows = [dict(label="Counter sale", href=P["approvals"], note=("Marg's own bills, %d of %d days" % (m["marg_days"], m["days"])) if m.get("marg_days") else "%d days" % m["days"],
                     cash=int(m["cash_p"] or 0), upi=int(m["upi_p"] or 0), card=0, two=0, total=int(m["sale_p"] or 0))]
        for k, lab in (("home_p", "− Home medicines"), ("proc_p", "− Procedure medicines"), ("other_p", "− Other")):
            v = int(m.get(k) or 0)
            if v:
                rows.append(dict(label=lab, href=P["approvals"], note="", cash=-v, upi=0, card=0, two=0, total=-v, neg=True))
        try:
            import returns_kinds                                       # noqa: PLC0415
            f = returns_kinds.month_fields(con, "medical", ym)
            if f.get("counter_returns_p"):
                rows.append(dict(label="− Counter returns · %d" % (f.get("counter_returns_n") or 0), href=P["approvals"], note="", cash=-int(f["counter_returns_p"]), upi=0, card=0, two=0,
                                 total=-int(f["counter_returns_p"]), neg=True))
        except Exception:                                              # noqa: BLE001 -- returns are a note, not the figure
            pass
        sub = _zero()
        for r in rows:
            _add(sub, r)
        heads.append(dict(key="sanj", title="Sanjeevni — counter", href=P["approvals"], links=[dict(t="approvals", href=P["approvals"]), dict(t="Darpan's month", href=P["dkal"])],
                          rows=rows, sub=dict(label="Sanjeevni subtotal", **sub), days=int(m["days"] or 0)))
    piece_h(sanj, "Sanjeevni's revenue", heads, un)

    def physio():
        rows = []
        if _has(con, "clinic_physio_day"):
            r = _q(con, "SELECT COALESCE(SUM(cash_p),0), COALESCE(SUM(upi_p),0), COUNT(*) FROM clinic_physio_day WHERE business_date BETWEEN ? AND ?", (d0, d1)).fetchone()
            rows.append(dict(label="In-clinic · %d days" % r[2], href=P["physio"], note="reception's counter sheet", cash=int(r[0]), upi=int(r[1]), card=0, two=0, total=int(r[0]) + int(r[1])))
        home = None
        if _has(con, "physio_session") and _has(con, "physio_course"):
            v = _q(con, "SELECT COUNT(*), COALESCE(SUM(s.amount_p),0) FROM physio_session s JOIN physio_course c ON c.id=s.course_id "
                            "WHERE c.kind='home' AND s.day BETWEEN ? AND ? AND s.voided_at IS NULL", (d0, d1)).fetchone()
            p = _q(con, "SELECT COALESCE(SUM(p.amount_p),0) FROM physio_payment p JOIN physio_course c ON c.id=p.course_id "
                            "WHERE c.kind='home' AND p.day BETWEEN ? AND ? AND p.voided_at IS NULL", (d0, d1)).fetchone()[0]
            home = dict(visits=int(v[0]), charged=int(v[1]), received=int(p or 0))
        sub = _zero()
        for r in rows:
            _add(sub, r)
        heads.append(dict(key="physio", title="Physiotherapy", href=P["physio"], links=[dict(t="day table", href=P["physio"])], rows=rows,
                          sub=dict(label="Physiotherapy subtotal", **sub), home=home,
                          home_note="Bhati's own register · ₹500 a visit · kept apart from the accountants' income, as you ruled"))
    piece_h(physio, "physiotherapy", heads, un)
    tot = _zero()
    for h in heads:
        if h.get("sub"):
            _add(tot, h["sub"])
    cash, bank = tot["cash"], tot["upi"] + tot["card"] + tot["two"]
    pct = int(round(100.0 * cash / (cash + bank))) if (cash + bank) > 0 else None
    label = ("%s, grand total" if state == "ended" else "%s so far, grand total") % FULL[int(ym[5:7]) - 1]
    return dict(heads=heads, total=dict(label=label, **tot), cash_p=cash, bank_p=bank, cash_pct=pct, notes=notes,
                lists=dict(proc=(lf or {}).get("proc"), xray=(lf or {}).get("xray")) if lf else None, lists_href=P["lists"])


def piece_h(fn, what, heads, un):
    try:
        fn()
    except Exception as e:                                             # noqa: BLE001
        heads.append(dict(key="unread", title="%s: not read" % what, href=None, links=[], rows=[], sub=None, why="%s: %s" % (type(e).__name__, str(e)[:120])))
        un.append("%s: %s: %s" % (what, type(e).__name__, str(e)[:120]))


# ============================================================================================ X-ray expenses against revenue
def _film_prices(con, env, upto):
    """Per size: (price of the box last bought on or before `upto`, its bill day, source) from the Scan App's bills, read-only.
    xf_purchase (the film log's own copy of the Scan App's film bills) names the bill; assets.db gives its amount."""
    out = {z: None for z in SIZES}
    a = env.get("assets")
    if not a or not os.path.exists(a):
        return out, "the Scan App's database is not here"
    ac = _ro(a)
    try:
        bcols = {r[1] for r in ac.execute("PRAGMA table_info(bills)")} if _has(ac, "bills") else set()
        for z in SIZES:
            for r in _q(con, "SELECT src, bill_day, boxes FROM xf_purchase WHERE size=? AND gone_at='' AND held=0 AND bill_day<=? ORDER BY bill_day DESC, id DESC LIMIT 6", (z, upto)):
                boxes = float(r["boxes"] or 0)
                if boxes <= 0:
                    continue
                src = str(r["src"] or "")
                amt = None
                if src.startswith("bill:") and "total_amount" in bcols:
                    bid = src.split(":")[1]
                    b = ac.execute("SELECT total_amount FROM bills WHERE id=?", (bid,)).fetchone()
                    if b and b[0] is not None:
                        # one bill may carry both sizes: share its total by the boxes of each size on xf_purchase
                        allb = _q(con, "SELECT COALESCE(SUM(boxes),0) FROM xf_purchase WHERE src LIKE ? AND gone_at=''", ("bill:%s:%%" % bid,)).fetchone()[0] or boxes
                        amt = float(b[0]) * 100.0 * boxes / float(allb)
                elif src.startswith("line:") and _has(ac, "xray_film_line"):
                    l = ac.execute("SELECT amount FROM xray_film_line WHERE id=?", (src.split(":")[1],)).fetchone()
                    if l and l[0] is not None:
                        amt = float(l[0]) * 100.0
                if amt:
                    out[z] = dict(box_p=int(round(amt / boxes)), day=r["bill_day"], boxes=boxes, bill_p=int(round(amt)))
                    break
    finally:
        ac.close()
    return out, ""


def xray(con, env, ym, today, state, un, lf):
    d0, d1 = _first(ym), min(_last(ym), today)
    out = dict(ok=True, revenue_p=0, films=[], fixed=[], expense_p=0, notes=[], films_href=P["film"], bills_href=P["xcost"], lists_href=P["lists"])
    try:
        out["revenue_p"] = int(lf["xray"]["amt"]) if lf else int(_q(con, "SELECT COALESCE(SUM(xray_amount_p),0) FROM clinic_day_revenue WHERE business_date BETWEEN ? AND ?",
                                                                               (d0.isoformat(), d1.isoformat())).fetchone()[0])
        out["revenue_n"] = int(lf["xray"]["n"]) if lf else None
        # Docterz's own X-ray head for the same days, so the page can say when the slips and Docterz differ
        if _has(con, "clinic_day_revenue"):
            out["docterz_p"] = int(_q(con, "SELECT COALESCE(SUM(xray_amount_p),0) FROM clinic_day_revenue WHERE business_date BETWEEN ? AND ?",
                                               (d0.isoformat(), d1.isoformat())).fetchone()[0])
    except Exception as e:                                             # noqa: BLE001
        out["notes"].append("revenue not read: %s" % str(e)[:80])
    try:
        import xray_film as XF                                         # noqa: PLC0415
        used = XF.slip_films(con, d0, d1)                              # {size: films}
    except Exception as e:                                             # noqa: BLE001
        used = {}
        out["notes"].append("films used not read: %s" % str(e)[:80])
    try:
        prices, why = _film_prices(con, env, d1.isoformat())
    except Exception as e:                                             # noqa: BLE001
        prices, why = {z: None for z in SIZES}, "film prices not read: %s" % str(e)[:80]
    if why:
        out["notes"].append(why)
    for z in SIZES:
        n = int(used.get(z) or 0)
        pr = prices.get(z)
        rate = int(round(pr["box_p"] / float(FILMS_PER_BOX))) if pr else None
        amt = n * rate if (rate is not None) else None
        out["films"].append(dict(size=SIZE_LABEL[z], qty=n, rate_p=rate, amount_p=amt, box_p=pr["box_p"] if pr else None, box_day=pr["day"] if pr else None,
                                 note=("box ₹%s ÷ %d films · bought %s" % (_inr(pr["box_p"]), FILMS_PER_BOX, dm(pr["day"]))) if pr else "no film bill with an amount read yet"))
        if amt is not None:
            out["expense_p"] += amt
    nosize = int(used.get("", 0) or 0)
    if nosize:
        out["notes"].append("%d film%s on studies with no size set are not costed." % (nosize, "" if nosize == 1 else "s"))
    # the fixed costs, the month's share -- the machines and battery places MARKED X-ray on the Scan App's X-ray costs page,
    # spread the way that page spreads them (an AMC/CMC/insurance over its cover months; a battery over its place's usual life;
    # a service spend on its day). Read-only on assets.db; the page itself stays the authority.
    try:
        a = env.get("assets")
        if not a or not os.path.exists(a):
            raise FileNotFoundError("the Scan App's database is not here")
        ac = _ro(a)
        try:
            fixed = _xray_fixed(ac, ym)
        finally:
            ac.close()
        for f in fixed:
            out["fixed"].append(f)
            out["expense_p"] += int(f["amount_p"])
        if not fixed:
            out["notes"].append("No AMC, battery or service cost of the X-ray falls in this month (the X-ray costs page's marks).")
    except Exception as e:                                             # noqa: BLE001
        out["fixed_unread"] = "the fixed costs (AMC, batteries) could not be read here: %s -- see the X-ray costs page" % str(e)[:80]
    out["margin_p"] = out["revenue_p"] - out["expense_p"]
    out["pct"] = int(round(100.0 * out["margin_p"] / out["revenue_p"])) if out["revenue_p"] > 0 else None
    out["caption"] = ("Films at the price of the box last bought (%d a box); fixed costs by the month as the X-ray costs page spreads them. "
                      "The machine's own cost and electricity are not in it." % FILMS_PER_BOX)
    return out


def _months_between(a, b):
    """Whole months from the month of a to the month of b, inclusive; 0 when either is missing or b < a."""
    try:
        da, db_ = dt.date.fromisoformat(str(a)[:10]), dt.date.fromisoformat(str(b)[:10])
    except (TypeError, ValueError):
        return 0
    n = (db_.year - da.year) * 12 + (db_.month - da.month) + 1
    return n if n > 0 else 0


def _in_span(ym, a, b):
    try:
        return str(a)[:7] <= ym <= str(b)[:7]
    except TypeError:
        return False


def _xray_fixed(ac, ym):
    """The X-ray's own fixed costs falling in month ym, in paise, as the X-ray costs page would spread them."""
    out = []
    if not _has(ac, "xray_mark"):
        return out
    mc = {r[1] for r in ac.execute("PRAGMA table_info(xray_mark)")}
    live = "COALESCE(removed_at,'')=''" if "removed_at" in mc else "COALESCE(removed_by,'')=''"
    machines = [r[0] for r in ac.execute("SELECT ref_id FROM xray_mark WHERE kind='machine' AND %s" % live)]
    places = [r[0] for r in ac.execute("SELECT ref_id FROM xray_mark WHERE kind='battery_place' AND %s" % live)]
    names = {}
    if _has(ac, "assets"):
        for mid in machines:
            r = ac.execute("SELECT name FROM assets WHERE id=?", (mid,)).fetchone()
            names[mid] = (r[0] if r else "machine %s" % mid)
    # covers: AMC / CMC / insurance with a cost, spread over their months
    if machines and _has(ac, "asset_cover"):
        for mid in machines:
            for c in ac.execute("SELECT kind, provider, from_day, till_day, cost FROM asset_cover WHERE asset_id=? AND COALESCE(voided_at,'')='' "
                                "AND kind IN ('amc','cmc','insurance') AND cost IS NOT NULL", (mid,)):
                n = _months_between(c["from_day"], c["till_day"])
                if n and _in_span(ym, c["from_day"], c["till_day"]):
                    out.append(dict(label="%s · %s" % (names.get(mid, "machine"), (c["kind"] or "").upper() if c["kind"] in ("amc", "cmc") else "Insurance"),
                                    amount_p=int(round(float(c["cost"]) * 100 / n)), note="₹%s over %d months · %s" % (_inr(int(float(c["cost"]) * 100)), n, (c["provider"] or "")[:30])))
    # service spends on their day
    if machines and _has(ac, "service_logs"):
        for mid in machines:
            for s in ac.execute("SELECT log_date, work, cost FROM service_logs WHERE asset_id=? AND cost IS NOT NULL AND substr(log_date,1,7)=?", (mid, ym)):
                out.append(dict(label="%s · service" % names.get(mid, "machine"), amount_p=int(round(float(s["cost"]) * 100)), note="%s · %s" % (dm(s["log_date"]), (s["work"] or "")[:40])))
    # batteries: each fit's price over the place's usual life, from the month it was fitted
    if places and _has(ac, "battery_fit") and _has(ac, "battery_place"):
        fc = {r[1] for r in ac.execute("PRAGMA table_info(battery_fit)")}
        dcol = next((c for c in ("fitted_on", "fit_day", "day", "fitted", "on_day", "at") if c in fc), None)
        if dcol:
            for pid in places:
                p = ac.execute("SELECT name, life_months FROM battery_place WHERE id=?", (pid,)).fetchone()
                life = int(p["life_months"] or 12) if p else 12
                for f in ac.execute("SELECT %s AS d, price FROM battery_fit WHERE place_id=? AND COALESCE(voided_at,'')='' AND price IS NOT NULL" % dcol, (pid,)):
                    d0 = str(f["d"] or "")[:10]
                    if len(d0) < 7:
                        continue
                    y, m = int(d0[:4]), int(d0[5:7])
                    end = dt.date(y + (m - 1 + life - 1) // 12, (m - 1 + life - 1) % 12 + 1, 1)
                    if _in_span(ym, d0, end.isoformat()):
                        out.append(dict(label="%s · battery" % ((p["name"] if p else "battery place")[:30]), amount_p=int(round(float(f["price"]) * 100 / life)),
                                        note="₹%s over %d months from %s" % (_inr(int(float(f["price"]) * 100)), life, dm(d0))))
    return out


# ============================================================================================ bought for the rooms
def bought(con, env, ym, today, state, un):
    d0, d1 = _first(ym).isoformat(), _last(ym).isoformat()
    rows, total = [], 0
    # film bills of the month (xf_purchase, the Scan App's bills as the film log copies them)
    try:
        prices, _why = _film_prices(con, env, d1)
        for z in SIZES:
            rs = _q(con, "SELECT src, bill_day, boxes, vendor FROM xf_purchase WHERE size=? AND gone_at='' AND bill_day BETWEEN ? AND ? ORDER BY bill_day", (z, d0, d1)).fetchall()
            if not rs:
                continue
            boxes = sum(float(r["boxes"] or 0) for r in rs)
            pr = prices.get(z)
            amt = int(round(boxes * pr["box_p"])) if pr else None
            if amt:
                total += amt
            rows.append(dict(k="X-ray films · %s" % SIZE_LABEL[z], sub="%g box%s · %s · %s" % (boxes, "" if boxes == 1 else "es", (rs[0]["vendor"] or "film bill")[:30], ", ".join(dm(r["bill_day"]) for r in rs)),
                             v=("₹%s" % _inr(amt)) if amt is not None else "amount not read", href=P["xcost"], st="", cls=""))
    except Exception as e:                                             # noqa: BLE001
        rows.append(dict(k="X-ray film bills", sub="not read: %s" % str(e)[:80], v="—", href=P["xcost"], st="", cls="w"))
    # the consumables lanes, from the Scan App's bills (read-only): clinic consumables and its sub-groups, by bill month
    try:
        a = env.get("assets")
        if not a or not os.path.exists(a):
            raise FileNotFoundError("the Scan App's database is not here")
        ac = _ro(a)
        try:
            bcols = {r[1] for r in ac.execute("PRAGMA table_info(bills)")}
            if not {"subgroup", "total_amount"} <= bcols:
                raise RuntimeError("the Scan App has no bill groups yet")
            dcol = "bill_date" if "bill_date" in bcols else "created_at"
            where = "substr(COALESCE(%s, created_at),1,7)=? AND COALESCE(status,'')<>'rejected'" % dcol + (" AND dup_of IS NULL" if "dup_of" in bcols else "")
            groups = ac.execute("SELECT COALESCE(subgroup,'') AS sg, COUNT(*), COALESCE(SUM(total_amount),0) FROM bills WHERE %s GROUP BY 1 ORDER BY 3 DESC" % where, (ym,)).fetchall()
        finally:
            ac.close()
        shown = 0
        for g in groups:
            sg = str(g[0] or "")
            if sg.startswith("xray_") or not sg:
                continue
            amt = int(round(float(g[2] or 0) * 100))
            total += amt
            shown += 1
            rows.append(dict(k=sg.replace("_", " ").capitalize(), sub="%d bill%s · the Scan App's lane" % (g[1], "" if g[1] == 1 else "s"), v="₹%s" % _inr(amt), href=P["papers"], st="", cls=""))
        unl = next((g for g in groups if not str(g[0] or "")), None)
        if unl and unl[1]:
            rows.append(dict(k="Bills not yet laned", sub="%d bill%s waiting for a group" % (unl[1], "" if unl[1] == 1 else "s"), v="₹%s" % _inr(int(round(float(unl[2] or 0) * 100))),
                             href=P["papers"], st="lane not settled", cls="w"))
        if not shown and not unl:
            rows.append(dict(k="Room consumables", sub="no bill of this month in the lanes", v="—", href=P["papers"], st="", cls=""))
    except Exception as e:                                             # noqa: BLE001
        rows.append(dict(k="Room consumables", sub="not read: %s" % str(e)[:80], v="—", href=P["papers"], st="", cls="w"))
    return dict(rows=rows, total_p=total, n=len(rows), caption="Bills of the month, not the cost of the month's work: a box bought on the 28th is used next month. "
                "Only films have a true per-use figure, from the log.")


# ============================================================================================ supplies and replacements
def supplies(con, env, ym, today, state, un):
    rows = []
    a = env.get("assets")
    if not a or not os.path.exists(a):
        return dict(rows=[dict(k="Stationery, batteries, machines", sub="the Scan App's database is not here", v="—", href=P["station"], st="", cls="w")], n=1)
    try:
        ac = _ro(a)
    except sqlite3.Error as e:
        return dict(rows=[dict(k="Stationery, batteries, machines", sub="not read: %s" % str(e)[:60], v="—", href=P["station"], st="", cls="w")], n=1)
    d0, d1 = _first(ym).isoformat(), _last(ym).isoformat()
    try:
        # stationery: the challan lines of the month, clinic and NK apart; the monthly statement made or not
        try:
            if _has(ac, "stationery_line"):
                lc = {r[1] for r in ac.execute("PRAGMA table_info(stationery_line)")}
                dcol = "day" if "day" in lc else ("created_at" if "created_at" in lc else None)
                side = "side" if "side" in lc else None
                amtc = next((c for c in ("amount", "total", "line_total", "value") if c in lc), None)
                void = "AND COALESCE(voided_at,'')=''" if "voided_at" in lc else ""
                if dcol:
                    q = "SELECT %s, COUNT(*), %s FROM stationery_line WHERE substr(%s,1,10) BETWEEN ? AND ? %s GROUP BY 1" % (
                        side or "'clinic'", ("COALESCE(SUM(%s),0)" % amtc) if amtc else "0", dcol, void)
                    parts = {str(r[0] or "clinic"): (r[1], float(r[2] or 0)) for r in ac.execute(q, (d0, d1))}
                    n = sum(v[0] for v in parts.values())
                    words = " · ".join("%s %d line%s%s" % ("NK Pathology" if k == "nk" else "clinic", v[0], "" if v[0] == 1 else "s", (" ₹%s" % _inr(int(v[1] * 100))) if amtc and v[1] else "")
                                       for k, v in parts.items())
                    st, cls = "", ""
                    if _has(ac, "stationery_stmt"):
                        sc = {r[1] for r in ac.execute("PRAGMA table_info(stationery_stmt)")}
                        mcol = "ym" if "ym" in sc else ("month" if "month" in sc else None)
                        if mcol:
                            s = ac.execute("SELECT made_at FROM stationery_stmt WHERE %s=? AND COALESCE(voided_at,'')='' ORDER BY id DESC LIMIT 1" % mcol, (ym,)).fetchone()
                            st, cls = ("statement made %s" % when(s[0]), "g") if s else (("monthly statement not made yet -- one tap", "w") if n else ("", ""))
                    rows.append(dict(k="Stationery · the challans", sub=words or "no challan line this month", v="%d line%s" % (n, "" if n == 1 else "s"), href=P["station"], st=st, cls=cls))
                else:
                    rows.append(dict(k="Stationery", sub="the challan lines carry no day column", v="—", href=P["station"], st="", cls=""))
            else:
                rows.append(dict(k="Stationery", sub="no stationery tables yet", v="—", href=P["station"], st="", cls=""))
        except Exception as e:                                         # noqa: BLE001
            rows.append(dict(k="Stationery", sub="not read: %s" % str(e)[:80], v="—", href=P["station"], st="", cls="w"))
        # batteries fitted or replaced in the month
        try:
            if _has(ac, "battery_fit"):
                fc = {r[1] for r in ac.execute("PRAGMA table_info(battery_fit)")}
                dcol = next((c for c in ("fitted_on", "fit_day", "day", "fitted_at", "created_at") if c in fc), None)
                void = "AND COALESCE(voided_at,'')=''" if "voided_at" in fc else ""
                if dcol:
                    r = ac.execute("SELECT COUNT(*), COALESCE(SUM(%s),0) FROM battery_fit WHERE substr(%s,1,10) BETWEEN ? AND ? %s" % ("price" if "price" in fc else "0", dcol, void), (d0, d1)).fetchone()
                    n = int(r[0] or 0)
                    bw = 0
                    if "bill_id" in fc or "paper" in fc:
                        pc = "bill_id" if "bill_id" in fc else "paper"
                        bw = ac.execute("SELECT COUNT(*) FROM battery_fit WHERE substr(%s,1,10) BETWEEN ? AND ? %s AND COALESCE(%s,'') IN ('', 'none:awaited')" % (dcol, void, pc), (d0, d1)).fetchone()[0]
                    rows.append(dict(k="Batteries fitted or replaced", sub=("%d this month" % n) if n else "none this month", v=("₹%s" % _inr(int(float(r[1] or 0) * 100))) if n else "—",
                                     href=P["batt"], st=("%d bill%s awaited" % (bw, "" if bw == 1 else "s")) if bw else "", cls="w" if bw else ""))
                else:
                    rows.append(dict(k="Batteries", sub="the fits carry no day column", v="—", href=P["batt"], st="", cls=""))
            else:
                rows.append(dict(k="Batteries", sub="no battery places yet", v="—", href=P["batt"], st="", cls=""))
        except Exception as e:                                         # noqa: BLE001
            rows.append(dict(k="Batteries", sub="not read: %s" % str(e)[:80], v="—", href=P["batt"], st="", cls="w"))
        # machines: service logs and new assets in the month
        try:
            n_srv = ac.execute("SELECT COUNT(*) FROM service_logs WHERE substr(log_date,1,10) BETWEEN ? AND ?", (d0, d1)).fetchone()[0] if _has(ac, "service_logs") else 0
            acols = {r[1] for r in ac.execute("PRAGMA table_info(assets)")} if _has(ac, "assets") else set()
            n_new = ac.execute("SELECT COUNT(*) FROM assets WHERE substr(purchase_date,1,10) BETWEEN ? AND ?", (d0, d1)).fetchone()[0] if "purchase_date" in acols else 0
            nxt = ac.execute("SELECT MIN(next_due) FROM service_logs WHERE next_due > ?", (today.isoformat(),)).fetchone()[0] if _has(ac, "service_logs") else None
            rows.append(dict(k="Machines", sub="%d serviced · %d added this month" % (n_srv, n_new), v=("next service due %s" % dm(nxt)) if nxt else "—", href=P["machines"], st="", cls=""))
        except Exception as e:                                         # noqa: BLE001
            rows.append(dict(k="Machines", sub="not read: %s" % str(e)[:80], v="—", href=P["machines"], st="", cls="w"))
    finally:
        ac.close()
    return dict(rows=rows, n=len(rows))


# ============================================================================================ one month
def read_month(con, env, ym, today, state):
    un = []
    try:
        lf = lists_figures(con, ym, today)
    except Exception as e:                                             # noqa: BLE001
        lf = None
        un.append("the lists: %s: %s" % (type(e).__name__, str(e)[:120]))
    groups = [g_attendance(con, env, ym, today, state, un), g_sanjeevni(con, env, ym, today, state, un), g_darpan(con, env, ym, today, state, un),
              g_rooms(con, env, ym, today, state, un, lf), g_petty(con, env, ym, today, state, un), g_pack(con, env, ym, today, state, un),
              g_ipd(con, env, ym, today, state, un)]
    def _safe(fn, stub, what):
        try:
            return fn()
        except Exception as e:                                         # noqa: BLE001 -- one part never takes the month down
            un.append("%s: %s: %s" % (what, type(e).__name__, str(e)[:120]))
            return stub
    rev = _safe(lambda: revenue(con, env, ym, today, state, un, lf),
                dict(heads=[], total=dict(label="not read", **_zero()), cash_p=0, bank_p=0, cash_pct=None, notes=["the revenue could not be read"], lists=None, lists_href=P["lists"]), "the revenue")
    xr = _safe(lambda: xray(con, env, ym, today, state, un, lf), None, "the X-ray expenses")
    bt = _safe(lambda: bought(con, env, ym, today, state, un), dict(rows=[], total_p=0, n=0, caption="not read"), "bought for the rooms")
    sp = _safe(lambda: supplies(con, env, ym, today, state, un), dict(rows=[], n=0), "the supplies")
    done = sum(g["done"] for g in groups)
    yours = sum(g["yours"] for g in groups)
    n = sum(g["n"] for g in groups)
    waiting = sum(g["waiting"] for g in groups)
    sent = any(r["dot"] == "g" and r["text"].startswith("Pack sent") for r in groups[5]["rows"])
    due = _first(_next(ym)) + dt.timedelta(days=9)
    first_act = next((dict(t=g["act"], href=g["act_href"]) for g in groups if g.get("act")), None)
    summ = dict(done=done, yours=yours, waiting=waiting, n=n, pack_sent=sent, pack_due=due.isoformat(), pack_late=(state == "ended" and today > due and not sent),
                revenue_p=rev["total"]["total"], cash_pct=rev["cash_pct"], first_act=first_act,
                day_of=(today.day if state == "running" else None), days_in=_last(ym).day)
    return dict(ym=ym, label=mname(ym), state=state, summary=summ, groups=groups, revenue=rev, xray=xr, bought=bt, supplies=sp, unread=un)


def read(con, env, now=None):
    """The reading for the console's snapshot: the month before now (ended) and the running month."""
    now = now or dt.datetime.now()
    today = now.date()
    cur = today.strftime("%Y-%m")
    prev = _prev(cur)
    months = [read_month(con, env, prev, today, "ended"), read_month(con, env, cur, today, "running")]
    return dict(ok=True, version=VERSION, built=now.replace(microsecond=0).isoformat(), months=months, page="/finance/console/month")


def section_lines(month_reading):
    """The console section's lines: one per month, then one per group of the ended month that needs the owner."""
    lines = []
    if not month_reading or not month_reading.get("ok"):
        return lines
    for m in month_reading["months"]:
        s = m["summary"]
        if m["state"] == "ended":
            text = "%s: %d of %d steps done · %d need your hand · pack %s" % (m["label"], s["done"], s["n"], s["yours"],
                                                                                "sent" if s["pack_sent"] else ("LATE" if s["pack_late"] else "due %s" % dm(s["pack_due"])))
            dot = "g" if (s["yours"] == 0 and s["pack_sent"]) else ("b" if s["pack_late"] else "w")
        else:
            text = "%s so far: ₹%s%s · day %d of %d" % (m["label"], _inr(s["revenue_p"]), (" · cash %d%%" % s["cash_pct"]) if s["cash_pct"] is not None else "", s["day_of"], s["days_in"])
            dot = "n"
        lines.append(dict(dot=dot, text=text, href="/finance/console/month#%s" % m["ym"], link="the month"))
        if m["state"] == "ended":
            for g in m["groups"]:
                if g["yours"]:
                    lines.append(dict(dot="w", text="%s · %s" % (g["title"], g["sub"][0]["t"] if g["sub"] else "%d need you" % g["yours"]),
                                      href=g.get("act_href") or g["href"], link=g["act"] or "open", sub=True))
    return lines
