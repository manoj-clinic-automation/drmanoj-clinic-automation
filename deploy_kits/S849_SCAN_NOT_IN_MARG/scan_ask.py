#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scan_ask.py -- S849_SCAN_NOT_IN_MARG (17-Nov-2026, Sanjeevni session 473; D993, D995; F-1433).

THE OWNER, 16-Nov-2026 12:00-12:34 IST: "1 is my job to see along with amir, and both can correct it"; 17-Nov 11:32: "take the example of
Deepam Pharma. It should open all the scans suggested by you ... in line, and the Marg lines, and what we have written should be more easy to
grasp"; "ok" (11:38) on mock-up v2 (https://claude.ai/artifact/FY6ubLCgQTww6g3Aqsjjzh).

WHAT: a pharmacy scan that is still on Amir's "Marg mein daalne ke bill" list (purchase_app.scans_for_amir -- unlinked, not a second scan,
supplier known) after Marg's purchases have moved `purchase.not_in_marg_days` (7) days past the bill's date is ASKED -- of the doctor (Needs
you -> the page below) and of Amir (first on his card) -- with the scan and each Marg bill of that dealer from those days (its own scan and its
lines) side by side. The first answer closes it for both:
  same   -- "this is Marg bill X": the scan is joined to X (CONFIRMED), or kept as X's second scan when X already has one (dup_ok, as the
            reception's 'Yahi bill hai?' does); the matcher then re-runs;
  enter  -- "another bill -- Amir enters it in Marg": the scan stays on Amir's enter list (as before) and leaves by itself when Marg's export
            carries it. Still not in Marg once Marg's purchases run the same days past the answer -> asked of the doctor again;
  notbill-- "not a purchase bill": the scan leaves every purchase list (scans_for_amir, provisional_s781.provisional), recorded.
Scans of a month before `purchase.register_from` (the parked months) are the doctor's only, folded.
Writes: its own table s849_answer, purchase_scan_link / purchase_bill.scan_bill_id / purchase_scan_state (the 'same' answer, exactly as the
reception's confirm), purchase_audit, setting purchase.not_in_marg_days. assets.db READ ONLY.
OFF: /root/finance/_off/ALL_OFF or /root/finance/_off/S849_OFF -- nothing asked, nothing set aside.
"""
import datetime as dt
import html
import json
import os
import re
import sqlite3
import sys

KIT = "S849_SCAN_NOT_IN_MARG"
VERSION = "S849-SCAN-ASK-1.0"
HERE = os.path.dirname(os.path.abspath(__file__))
OFF_FLAGS = (os.path.join(HERE, "_off", "ALL_OFF"), os.path.join(HERE, "_off", "S849_OFF"))
PAGE = "/finance/sanjeevni/not-in-marg"
SCAN_URL = "/finance/purchase/api/s738/scan/%d"
SET_DAYS = "purchase.not_in_marg_days"
DAYS_DEFAULT = 7
NEAR_DAYS = 20                         # a Marg bill of the dealer within 20 days of the paper's date is a candidate
MAX_CANDS = 4
DDL = ("CREATE TABLE IF NOT EXISTS s849_answer (id INTEGER PRIMARY KEY AUTOINCREMENT, scan INTEGER NOT NULL, answer TEXT NOT NULL, "
       "bill_id INTEGER, by_user TEXT, at TEXT NOT NULL, undone_at TEXT, undone_by TEXT)")
ANSWERS = ("same", "enter", "notbill")
EN = {"same": "the same bill as Marg bill %s", "enter": "another bill — Amir to enter it in Marg", "notbill": "not a purchase bill"}

_db = None
_require = None


def esc(s):
    return html.escape("" if s is None else str(s), quote=True)


def now_iso():
    return dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def is_off():
    return next((f for f in OFF_FLAGS if os.path.exists(f)), None)


def rs(p):
    if p is None:
        return "—"
    v = int(round(p))
    s, n = ("-" if v < 0 else ""), abs(v) // 100
    t = str(n)
    if len(t) > 3:
        head, tail = t[:-3], t[-3:]
        head = ",".join([head[max(0, i - 2):i] for i in range(len(head), 0, -2)][::-1])
        t = head + "," + tail
    return "%s₹%s" % (s, t)


def dmy(iso):
    try:
        d = dt.date.fromisoformat(str(iso)[:10])
        return d.strftime("%d-%b-%Y")
    except (TypeError, ValueError):
        return str(iso or "")


def dm_hi(iso):
    try:
        return dt.date.fromisoformat(str(iso)[:10]).strftime("%d-%m-%Y")
    except (TypeError, ValueError):
        return str(iso or "")


def _date(s):
    try:
        return dt.date.fromisoformat(str(s)[:10])
    except (TypeError, ValueError):
        return None


def PA():
    import purchase_app                                     # noqa: PLC0415 -- beside this file
    return purchase_app


def PV():
    import provisional_s781                                 # noqa: PLC0415
    return provisional_s781


def _table(con, name):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def ensure(con):
    con.execute(DDL)


def setting(con, key, default=""):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        return str(r[0]) if r and r[0] not in (None, "") else default
    except sqlite3.Error:
        return default


def days(con):
    try:
        v = int(setting(con, SET_DAYS, str(DAYS_DEFAULT)))
        return v if 1 <= v <= 60 else DAYS_DEFAULT
    except ValueError:
        return DAYS_DEFAULT


def set_days(con, who, n):
    n = int(n)
    if not 1 <= n <= 60:
        return False
    con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES (?,?,?)",
                (SET_DAYS, str(n), "S849: ask about a pharmacy scan not found in Marg once Marg's purchases are this many days past its bill (the owner's setting)"))
    _audit(con, who, "s849_setting", SET_DAYS, dict(value=n))
    con.commit()
    return True


def _audit(con, who, action, ref, detail):
    try:
        d = dict(detail or {})
        d.setdefault("kit", KIT)
        con.execute("INSERT INTO purchase_audit (at, who, action, ref, detail) VALUES (?,?,?,?,?)",
                    (now_iso(), who or "", action, str(ref or ""), json.dumps(d, sort_keys=True, default=str)))
    except sqlite3.Error as e:
        print("scan_ask audit failed: %s" % e, file=sys.stderr)


# ====================================================================== answers
def answers(con):
    """{scan: the newest answer not undone}."""
    if not _table(con, "s849_answer"):
        return {}
    out = {}
    for r in con.execute("SELECT id, scan, answer, bill_id, by_user, at FROM s849_answer WHERE undone_at IS NULL ORDER BY id"):
        out[int(r[1])] = dict(id=int(r[0]), scan=int(r[1]), answer=r[2], bill_id=r[3], by=r[4], at=r[5])
    return out


def aside_ids(con):
    """The scans answered 'not a purchase bill' -- they leave every purchase list. Empty when OFF or on any error."""
    if is_off():
        return set()
    try:
        return {s for s, a in answers(con).items() if a["answer"] == "notbill"}
    except Exception:                                         # noqa: BLE001
        return set()


# ====================================================================== who is asked, and about what
def marg_reach(con):
    """The newest bill date in Marg's purchase register ('' when none)."""
    try:
        r = con.execute("SELECT MAX(bill_date) FROM purchase_bill").fetchone()
        return str(r[0] or "")[:10]
    except sqlite3.Error:
        return ""


def _scan_rows():
    try:
        rows = PA()._s452_scan_rows()
    except Exception:                                         # noqa: BLE001
        rows = None
    return {int(r["id"]): r for r in (rows or [])}


def _amount_p(v):
    try:
        return int(round(float(str(v).replace(",", "")) * 100)) if v not in (None, "") else None
    except ValueError:
        return None


def marg_lines(con, b):
    """Marg's own lines of one bill, from the newest export that carries them: name, qty, free, rate, batch, expiry."""
    try:
        rows = [dict(r) for r in con.execute(
            "SELECT item, qty, free, rate_p, batch, expiry, source_md5, id FROM purchase_line WHERE supplier_norm=? AND bill_no=? AND bill_date=? "
            "AND COALESCE(direction,'PURCHASE')='PURCHASE' ORDER BY id", (b["supplier_norm"], b["bill_no"], b["bill_date"]))]
    except sqlite3.Error:
        return []
    if not rows:
        return []
    newest = rows[-1]["source_md5"]
    out = []
    for r in rows:
        if r["source_md5"] != newest:
            continue
        out.append(dict(name=str(r["item"] or ""), qty=_num(r["qty"]), free=_num(r["free"]),
                        rate=(r["rate_p"] / 100.0) if r["rate_p"] is not None else None, batch=str(r["batch"] or ""), expiry=str(r["expiry"] or "")))
    return out


def _num(v):
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _bnorm(s):
    return re.sub(r"\W", "", str(s or "").upper())


def _exp(s):
    try:
        return PA()._s446_exp(s)
    except Exception:                                         # noqa: BLE001
        return str(s or "").strip()


def compare(slines, mlines):
    """[(scan line | None, marg line | None, marks)] -- marks: {qty, rate, batch, expiry: True/False/None}; and (lines agreed, lines read)."""
    pairs = PV().pair_lines(slines, mlines)
    out, agree = [], 0
    for a, m in pairs:
        mk = {}
        if a is not None and m is not None:
            q, f = m.get("qty"), m.get("free") or 0
            qa = a.get("qty")
            mk["qty"] = None if qa is None or q is None else any(abs(float(qa) - x) < 1e-6 for x in (q, q + f))
            ra, rm = a.get("rate"), m.get("rate")
            mk["rate"] = None if ra in (None, "") or rm is None else abs(float(ra) - rm) <= max(0.01, 0.01 * rm)
            ba, bm = _bnorm(a.get("batch")), _bnorm(m.get("batch"))
            mk["batch"] = None if not ba or not bm else ba == bm
            ea, em = _exp(a.get("expiry")), _exp(m.get("expiry"))
            mk["expiry"] = None if not ea or not em else ea == em
            if mk["batch"] is not False and mk["rate"] is not False:
                agree += 1
        out.append((a, m, mk))
    return out, agree


def _candidates(con, sup, base, total_p, slines, bill_no, link_of):
    """The dealer's Marg bills within NEAR_DAYS of the base date, best first: [dict(bill, lines, scan, agree, cmp, best)]."""
    pa = PA()
    if not sup or base is None:
        return []
    lo, hi = (base - dt.timedelta(days=NEAR_DAYS)).isoformat(), (base + dt.timedelta(days=NEAR_DAYS)).isoformat()
    rows = [dict(r) for r in con.execute("SELECT b.id, b.supplier, b.supplier_norm, b.bill_no, b.bill_date, b.amount_p, b.scan_bill_id FROM purchase_bill b "
                                         "WHERE b.bill_date BETWEEN ? AND ? AND b.amount_p>0 AND " + pa.EFF_BILL + " ORDER BY b.bill_date, b.id", (lo, hi))]
    rows = [b for b in rows if pa.supplier_key(b["supplier"]) == sup]
    out = []
    for b in rows:
        ml = marg_lines(con, b)
        cmp_, agree = compare(slines, ml) if slines and ml else ([], 0)
        sc = link_of.get(int(b["id"])) or (int(b["scan_bill_id"]) if b.get("scan_bill_id") else None)
        tail = False
        try:
            tail = bool(bill_no) and pa._s750_tail_match(bill_no, b["bill_no"]) if hasattr(pa, "_s750_tail_match") else False
        except Exception:                                     # noqa: BLE001
            tail = False
        if not tail and bill_no:
            da, db_ = re.sub(r"\D", "", str(bill_no)).lstrip("0"), re.sub(r"\D", "", str(b["bill_no"])).lstrip("0")
            tail = bool(da and db_) and len(min(da, db_, key=len)) >= 3 and (da.endswith(db_) or db_.endswith(da) or da in db_ or db_ in da)
        tot = total_p is not None and abs(int(b["amount_p"] or 0) - total_p) <= 200
        d = _date(b["bill_date"])
        out.append(dict(bill=b, lines=ml, scan=sc, agree=agree, n_scan=len(slines or []), cmp=cmp_, tail=tail, total=tot,
                        gap=abs((d - base).days) if d else 99))
    out.sort(key=lambda c: (-(c["agree"]), -int(c["tail"]), -int(c["total"]), c["gap"]))
    for c in out:
        c["best"] = False
    if out:
        top = out[0]
        full = top["n_scan"] > 0 and top["agree"] == top["n_scan"]
        alone = len(out) == 1 or (out[1]["agree"], out[1]["tail"], out[1]["total"]) != (top["agree"], top["tail"], top["total"])
        if alone and (full or (top["n_scan"] == 0 and (top["tail"] or top["total"]))):
            top["best"] = True
    return out[:MAX_CANDS]


def view(con, for_amir=False):
    """The cases. dict(ok, asked=[...], again=[...], parked=[...], enter=[...], reach, days, answered). The source is the Purchase bills page's
    own waiting list (provisional_s781.provisional, every month: a pharmacy scan with no Marg bill yet) -- one list, never a second. A case:
    dict(scan, stamp, supplier, sup, bill_no, paper_date, paper_total_p, base, lines, cands, answer). asked: waiting for an answer;
    again: answered 'enter' and still not in Marg past the days (the doctor only); parked: a month before purchase.register_from (the doctor
    only); enter: answered 'enter', not yet in Marg (Amir's do-line)."""
    out = dict(ok=False, asked=[], again=[], parked=[], enter=[], reach="", days=DAYS_DEFAULT, answered=[])
    if is_off():
        return out
    ensure(con)
    pa, P = PA(), PV()
    S = P.SR()
    scans = S.asset_scans(con)
    if scans is None:
        return out
    n_days = days(con)
    reach = _date(marg_reach(con))
    out.update(reach=reach.isoformat() if reach else "", days=n_days)
    if not for_amir and _table(con, "s849_answer"):
        out["answered"] = [dict(r) for r in _answered_rows(con)]
    if reach is None:
        out["ok"] = True
        return out
    ans = answers(con)
    reg_from = setting(con, "purchase.register_from", "")
    try:
        link_of = {int(x[0]): int(x[1]) for x in con.execute("SELECT bill_id, asset_bill_id FROM purchase_scan_link")}
    except sqlite3.Error:
        link_of = {}
    cx = S.Ctx(con)
    months = sorted({str(x.get("month") or "") for x in scans.values() if re.match(r"^\d{4}-\d\d$", str(x.get("month") or ""))})
    waiting = []
    for m in months:
        try:
            waiting += P.provisional(con, m, scans=scans, cx=cx)
        except Exception as e:                                # noqa: BLE001 -- one month's failure never hides the others
            print("scan_ask: the waiting list of %s could not be read: %s" % (m, str(e)[:160]), file=sys.stderr)
    for x in waiting:
        sid = int(x["id"])
        a = ans.get(sid)
        if a and a["answer"] in ("notbill", "same"):
            continue
        day, pd = _date(x.get("day")), _date(x.get("date"))
        base = pd if (pd and day and day - dt.timedelta(days=60) <= pd <= day + dt.timedelta(days=1)) else (day or pd)
        if base is None:
            continue
        if a and a["answer"] == "enter":
            since = _date(a["at"]) or base
            if reach >= max(base, since) + dt.timedelta(days=n_days) and not for_amir:
                kind = "again"
            else:
                kind = "enter"
        elif reach >= base + dt.timedelta(days=n_days):
            kind = "asked"
        else:
            continue
        if kind == "asked" and reg_from and base.isoformat()[:7] < reg_from[:7]:
            if for_amir:
                continue
            kind = "parked"
        sup = x["dealer"] if x.get("known") else ""
        c = dict(scan=sid, stamp=x.get("stamp") or "#%d" % sid, sup=sup, supplier=str(x.get("dealer") or "the dealer not read").title(),
                 bill_no=str(x.get("bill_no") or ""), paper_date=pd.isoformat() if (pd and base == pd) else "", paper_total_p=x.get("total_p"),
                 base=base.isoformat(), scan_day=x.get("day") or "", lines=x.get("lines") or [], answer=a, cands=[])
        if kind != "enter" or for_amir:
            c["cands"] = _candidates(con, sup, base, x.get("total_p"), c["lines"], c["bill_no"], link_of)
        out[kind].append(c)
    for k in ("asked", "again", "parked", "enter"):
        out[k].sort(key=lambda c: (c["base"], c["scan"]))
    out["ok"] = True
    return out


def _answered_rows(con):
    con2 = con
    rf = con2.row_factory
    try:
        con2.row_factory = sqlite3.Row
        return [dict(r) for r in con2.execute("SELECT a.id, a.scan, a.answer, a.bill_id, a.by_user, a.at, a.undone_at, b.bill_no, b.bill_date "
                                              "FROM s849_answer a LEFT JOIN purchase_bill b ON b.id=a.bill_id ORDER BY a.id DESC LIMIT 60")]
    finally:
        con2.row_factory = rf


def amir_ids(con):
    """The scans asked of Amir right now (they leave his plain enter list while asked)."""
    try:
        return {c["scan"] for c in view(con, for_amir=True)["asked"]}
    except Exception:                                         # noqa: BLE001
        return set()


def amir_may_see(con, sid):
    """Amir may open a scan shown on his card's question: the asked scan, or a candidate bill's own scan."""
    try:
        sid = int(sid)
        v = view(con, for_amir=True)
        for c in v["asked"] + v["enter"]:
            if sid == c["scan"] or sid in {x["scan"] for x in c["cands"] if x.get("scan")}:
                return True
    except Exception:                                         # noqa: BLE001
        pass
    return False


# ====================================================================== the answer (doctor or Amir)
def answer(con, who, sid, code, bill_id=None, owner=False):
    """(ok, message). The first answer closes the question for both. Only a scan asked right now can be answered (the doctor also
    the 'again' and parked ones); 'same' only with a bill among its candidates."""
    if is_off():
        return False, "This is switched off."
    if code not in ANSWERS:
        return False, "Unknown answer."
    ensure(con)
    v = view(con, for_amir=not owner)
    pool = v["asked"] + (v["again"] + v["parked"] if owner else [])
    case = next((c for c in pool if c["scan"] == int(sid)), None)
    if case is None:
        return False, "This scan is no longer waiting for an answer — the page has moved on; reload it."
    bid = None
    pa = PA()
    if code == "same":
        cand = next((x for x in case["cands"] if int(x["bill"]["id"]) == int(bill_id or 0)), None)
        if cand is None:
            return False, "That Marg bill is not one of this scan's candidates."
        bid = int(cand["bill"]["id"])
        taken = con.execute("SELECT asset_bill_id FROM purchase_scan_link WHERE bill_id=?", (bid,)).fetchone()
        other = int(taken[0]) if taken else (cand.get("scan") if cand.get("scan") and int(cand["scan"]) != int(sid) else None)
        pa._ensure_s439(con)
        con.execute("INSERT OR IGNORE INTO purchase_scan_state (asset_bill_id, why, detail, checked_at) VALUES (?,?,?,?)", (int(sid), "linked", "linked", now_iso()))
        if other and int(other) != int(sid):
            con.execute("UPDATE purchase_scan_state SET dup_ok=?, confirmed_by=?, confirmed_at=? WHERE asset_bill_id=?", (int(other), who, now_iso(), int(sid)))
            _audit(con, who, "scan_dup_confirmed", bid, dict(scan=int(sid), dup_cand=int(other), note="S849: the same bill, scanned twice"))
        else:
            con.execute("INSERT OR IGNORE INTO purchase_scan_link (bill_id, asset_bill_id, grade, matched_on, linked_at) VALUES (?,?,?,?,?)",
                        (bid, int(sid), "CONFIRMED", "%s answered (S849)" % ("owner" if owner else "amir"), now_iso()))
            con.execute("UPDATE purchase_bill SET scan_bill_id=? WHERE id=?", (int(sid), bid))
            con.execute("UPDATE purchase_scan_state SET confirmed_by=?, confirmed_at=? WHERE asset_bill_id=?", (who, now_iso(), int(sid)))
            _audit(con, who, "scan_link", bid, dict(scan=int(sid), grade="CONFIRMED", rule="S849 answer", bill_no=cand["bill"]["bill_no"]))
    con.execute("INSERT INTO s849_answer (scan, answer, bill_id, by_user, at) VALUES (?,?,?,?,?)", (int(sid), code, bid, who, now_iso()))
    _audit(con, who, "s849_answer", int(sid), dict(answer=code, bill=bid, owner=bool(owner)))
    con.commit()
    if code == "same":
        try:
            pa._rematch(con, who)
        except Exception as e:                                # noqa: BLE001 -- the link stands; the next rematch sees it
            print("scan_ask: rematch after the answer failed: %s" % str(e)[:200], file=sys.stderr)
    words = EN[code] % (cand["bill"]["bill_no"],) if code == "same" else EN[code]
    return True, "Recorded: %s is %s." % (case["stamp"], words)


def undo(con, who, aid):
    """The doctor takes back an 'enter' or 'not a purchase bill' answer (a join is taken back on the Purchase bills page)."""
    ensure(con)
    r = con.execute("SELECT id, scan, answer FROM s849_answer WHERE id=? AND undone_at IS NULL", (int(aid),)).fetchone()
    if not r or r[2] not in ("enter", "notbill"):
        return False, "Nothing to undo."
    con.execute("UPDATE s849_answer SET undone_at=?, undone_by=? WHERE id=?", (now_iso(), who, int(aid)))
    _audit(con, who, "s849_undo", int(r[1]), dict(answer=r[2], row=int(aid)))
    con.commit()
    return True, "Undone — the scan is asked again."


# ====================================================================== the Hub's Needs you
def needs_lines(con):
    try:
        v = view(con)
        n = len(v["asked"]) + len(v["again"])
        if not n:
            return []
        names = ", ".join("%s (%s)" % (c["supplier"], c["stamp"]) for c in (v["asked"] + v["again"])[:3]) + (" and %d more" % (n - 3) if n > 3 else "")
        return [dict(cls="warn", target="scans", href=PAGE,
                     text="Scanned bills not found in Marg — %d: %s" % (n, names))]
    except Exception:                                         # noqa: BLE001
        return []


# ====================================================================== Amir's card (Hindi)
def amir_view(cx):
    """(ids asked, [html blocks]) for his card. Fail-soft: (set(), [])."""
    try:
        v = view(cx, for_amir=True)
    except Exception as e:                                    # noqa: BLE001
        print("scan_ask: Amir's view failed: %s" % str(e)[:200], file=sys.stderr)
        return set(), []
    blocks = [_amir_block(c) for c in v["asked"]]
    for c in v["enter"]:
        blocks.append("<div class=line style='border-left:4px solid #e3a33b;padding-left:8px'><span class=big><b>Marg mein chadhaiye</b></span><br>"
                      "<span>%s &middot; scan %s &middot; %s</span><br><a class='btn plain' target=_blank rel=noopener href='%s'>Scan dekhiye</a>"
                      "<p class=sub>Marg ki kharid report mein aate hi yeh line apne aap hat jaayegi.</p></div>"
                      % (esc(c["supplier"]), esc(c["stamp"]), esc(dm_hi(c["paper_date"] or c["base"])), esc(SCAN_URL % c["scan"])))
    return {c["scan"] for c in v["asked"] + v["enter"]}, blocks


def _amir_block(c):
    best = next((x for x in c["cands"] if x["best"]), None)
    others = [x for x in c["cands"] if x is not best][:2 if best else 2]
    hd = ("<div class=line style='border-left:4px solid #b42318;padding-left:8px'><span class=big><b>Yeh scan kiya hua bill Marg mein nahi mila</b></span><br>"
          "<span>%s &middot; scan %s &middot; %s</span><br><a class='btn plain' target=_blank rel=noopener href='%s'>Scan dekhiye</a>"
          % (esc(c["supplier"]), esc(c["stamp"]), esc(dm_hi(c["paper_date"] or c["base"])), esc(SCAN_URL % c["scan"])))
    body = ""
    if best:
        b = best["bill"]
        rows = "".join("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (esc(m["name"]), esc(_qf(m)), esc(m.get("batch") or "")) for m in best["lines"][:8])
        same_w = "dawai, batch aur rate same hain:" if best["n_scan"] else "bill number ya total same hai:"
        body = ("<p class=sub style='margin:8px 0 4px'>Marg ka bill <b>%s</b> (%s, %s) &mdash; " + same_w + "</p>"
                "%s<table style='font-size:13px;margin:0 0 8px'>%s</table>")
        body = body % (esc(b["bill_no"]), esc(dm_hi(b["bill_date"])), esc(rs(b["amount_p"])),
                   ("<a class='btn plain' target=_blank rel=noopener href='%s'>Uska scan dekhiye</a>" % esc(SCAN_URL % best["scan"])) if best.get("scan") else "", rows)
    btn = []
    for x in ([best] if best else []) + others:
        b = x["bill"]
        btn.append(_amir_btn(c["scan"], "same", b["id"], ("<b>Haan &mdash; Marg ka bill %s hi hai</b> (%s)%s" if x is best else "Marg ka bill %s hai (%s)%s")
                             % (esc(b["bill_no"]), esc(dm_hi(b["bill_date"])), " &mdash; do baar scan hua" if (x is best and x.get("scan")) else "")))
    btn.append(_amir_btn(c["scan"], "enter", 0, "Doosra bill hai &mdash; Marg mein chadhata hoon" if c["cands"] else "Marg mein nahi hai &mdash; chadhata hoon"))
    btn.append(_amir_btn(c["scan"], "notbill", 0, "Yeh kharid ka bill nahi hai"))
    return hd + body + "".join(btn) + "</div>"


def _qf(m):
    q, f = m.get("qty"), m.get("free") or 0
    if q is None:
        return ""
    return ("%g + %g free" % (q, f)) if f else ("%g" % q)


def _amir_btn(sid, code, bid, label):
    return ("<form method=post style='margin:0 0 6px'><input type=hidden name=job value='sna:%d:%s:%d'>"
            "<button class='btn plain' style='display:block;width:100%%;text-align:left'>%s</button></form>" % (int(sid), code, int(bid or 0), label))


def amir_tap(cx, who, val):
    """'sna:<scan>:<code>:<bill>' from his card. Returns 1 when recorded, else 0. Never raises."""
    try:
        m = re.match(r"^sna:(\d{1,9}):(same|enter|notbill):(\d{1,9})$", str(val or ""))
        if not m:
            return 0
        ok, _msg = answer(cx, who, int(m.group(1)), m.group(2), int(m.group(3)) or None, owner=False)
        return 1 if ok else 0
    except Exception as e:                                    # noqa: BLE001
        try:
            cx.rollback()
        except Exception:                                     # noqa: BLE001
            pass
        print("scan_ask: Amir's tap failed: %s" % str(e)[:200], file=sys.stderr)
        return 0


# ====================================================================== the doctor's page
CSS = """
:root{--ink:#1d2430;--mute:#6b7380;--line:#e3e6ea;--bg:#f6f7f9;--green:#1d7a46;--greenbg:#ecfdf3;--red:#b42318;--redbg:#fdecea;--amber:#9a5b00;--amberbg:#fff4e0;--blue:#1570ef}
*{box-sizing:border-box}body{margin:0;font:14px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--ink);background:var(--bg)}
.wrap{max-width:1180px;margin:0 auto;padding:14px 20px 60px}.crumb{color:var(--mute);font-size:13px;margin-bottom:6px}.crumb a{color:inherit}
h1{font-size:22px;margin:0 0 6px}h2{font-size:15px;margin:18px 0 8px}.lead{color:var(--mute);margin:0 0 14px}
.case{background:#fff;border:1px solid var(--line);border-radius:10px;margin:0 0 10px}.case>summary{cursor:pointer;padding:11px 14px;list-style:none}
.case>summary::-webkit-details-marker{display:none}.case[open]>summary{background:#f9fafb;border-bottom:1px solid var(--line)}
.tag{display:inline-block;font-size:12px;border-radius:6px;padding:1px 7px;margin-left:6px}.t-ok{background:#dcfae6;color:#085d3a}.t-bad{background:#fee4e2;color:#912018}.t-grey{background:#f2f4f7;color:#475467}
.verdict{margin:10px 14px;padding:9px 12px;background:var(--greenbg);border:1px solid #abefc6;border-radius:8px;color:#054f31}
.verdict.no{background:#f9fafb;border-color:var(--line);color:var(--ink)}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:14px;padding:4px 14px 10px}.col{border:1px solid var(--line);border-radius:10px;padding:10px;min-width:0}
.colh{font-weight:600;margin:0 0 8px}.scanf{min-height:40px;margin:0 0 8px}.scanf iframe{width:100%;height:520px;border:1px solid var(--line);border-radius:6px}
table{width:100%;border-collapse:collapse}th{font-size:12px;color:var(--mute);text-align:left;font-weight:600;padding:5px 6px;border-bottom:1px solid var(--line)}
td{padding:5px 6px;border-bottom:1px solid #f0f1f3;vertical-align:top;font-size:13px}.ok{color:var(--green);font-weight:700}.bad{color:var(--red);font-weight:600}
.sub{color:var(--mute);font-size:12.5px}.more{margin:0 14px 10px}.more>summary{cursor:pointer;color:var(--blue);padding:6px 0}
.btns{display:flex;flex-wrap:wrap;gap:8px;padding:6px 14px 14px}.b{border:1px solid #c9ced6;background:#fff;border-radius:8px;padding:9px 13px;font:inherit;font-size:14px;cursor:pointer}
.b.pri{border-color:var(--blue);color:var(--blue);font-weight:600}.b.ghost{color:var(--mute)}.b[disabled]{opacity:.5;cursor:default}
.msg{margin:0 14px 10px;font-weight:600}.set{color:var(--mute);font-size:13px;margin:6px 0 14px}.set input{width:56px;padding:4px 6px;border:1px solid var(--line);border-radius:6px}
.note{background:var(--amberbg);border-left:4px solid #e3a33b;padding:8px 12px;margin:10px 14px;border-radius:6px}
@media(max-width:860px){.cols{grid-template-columns:1fr}}
"""

JS = """<script>
function s849open(d){ if(!d.open) return; d.querySelectorAll('.scanf[data-src]').forEach(function(f){ if(f.firstChild) return;
  var i=document.createElement('iframe'); i.loading='lazy'; i.src=f.getAttribute('data-src'); f.appendChild(i); }); }
document.querySelectorAll('details').forEach(function(d){ d.addEventListener('toggle',function(){ s849open(d); }); if(d.open) s849open(d); });
function s849post(btn, body){ var box=btn.closest('.case')||document.body; box.querySelectorAll('button').forEach(function(b){b.disabled=true;});
  fetch(PAGE+'/api/answer',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
  .then(function(r){return r.json().catch(function(){return {ok:false,message:'The server did not answer properly.'};});})
  .then(function(j){ var m=box.querySelector('.msg'); if(m){ m.textContent=j.message||''; m.style.color=j.ok?'#1d7a46':'#b42318'; }
    if(j.ok){ setTimeout(function(){ location.reload(); }, 900); } else { box.querySelectorAll('button').forEach(function(b){b.disabled=false;}); } })
  .catch(function(){ box.querySelectorAll('button').forEach(function(b){b.disabled=false;}); }); }
</script>"""


def _mark(v):
    return "" if v is None else (" <span class=ok>✓</span>" if v else " <span class=bad>✗</span>")


def _scan_table(lines):
    if not lines:
        return "<p class=sub>No item lines were read on this scan.</p>"
    rows = "".join("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
        esc(l.get("name")), esc("%g" % l["qty"] if l.get("qty") is not None else "—"), esc("%g" % l["rate"] if l.get("rate") not in (None, "") else "—"),
        esc(l.get("batch") or "—"), esc(l.get("expiry") or "—")) for l in lines[:40])
    return "<table><tr><th>Item as read</th><th>Qty</th><th>Rate</th><th>Batch</th><th>Exp</th></tr>%s</table>" % rows


def _cand_table(x):
    if not x["lines"]:
        return "<p class=sub>Marg's lines of this bill are not in the purchase export.</p>"
    if not x["cmp"]:
        rows = "".join("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            esc(m["name"]), esc(_qf(m)), esc("%.2f" % m["rate"] if m.get("rate") is not None else "—"), esc(m.get("batch") or "—"), esc(m.get("expiry") or "—"))
            for m in x["lines"][:40])
    else:
        rr = []
        for a, m, mk in x["cmp"]:
            if m is None:
                rr.append("<tr><td colspan=5 class=sub>%s — on the scan, not on this Marg bill</td></tr>" % esc(a.get("name")))
                continue
            q = esc(_qf(m)) + ((" <span class=sub>(scan read “%s”)</span>" % esc("%g" % a["qty"])) if a is not None and mk.get("qty") is False and a.get("qty") is not None else "")
            rr.append("<tr><td>%s%s</td><td>%s</td><td>%s%s</td><td>%s%s</td><td>%s%s</td></tr>" % (
                esc(m["name"]), _mark(True if a is not None else None) if a is not None else " <span class=sub>(not on the scan)</span>", q,
                esc("%.2f" % m["rate"] if m.get("rate") is not None else "—"), _mark(mk.get("rate")),
                esc(m.get("batch") or "—"), _mark(mk.get("batch")), esc(m.get("expiry") or "—"), _mark(mk.get("expiry"))))
        rows = "".join(rr)
    return "<table><tr><th>Item in Marg</th><th>Qty + free</th><th>Rate</th><th>Batch</th><th>Exp</th></tr>%s</table>" % rows


def _cand_col(x):
    b = x["bill"]
    tag = ("<span class='tag t-ok'>%d of %d lines agree</span>" % (x["agree"], x["n_scan"]) if x["n_scan"] and x["agree"] == x["n_scan"] else
           ("<span class='tag t-bad'>%d of %d lines</span>" % (x["agree"], x["n_scan"]) if x["n_scan"] else ""))
    sc = ("<div class=scanf data-src='%s'></div><div class=sub>its own scan B-%04d · <a target=_blank rel=noopener href='%s'>open in a new tab</a></div>"
          % (esc(SCAN_URL % x["scan"]), int(x["scan"]) % 10000, esc(SCAN_URL % x["scan"]))) if x.get("scan") else "<p class=sub>No scan joined to this Marg bill yet.</p>"
    return "<div class=col><div class=colh>Marg bill %s · %s · %s %s</div>%s%s</div>" % (esc(b["bill_no"]), esc(dmy(b["bill_date"])), esc(rs(b["amount_p"])), tag, sc, _cand_table(x))


def _case_html(c, open_=False, again=False):
    best = next((x for x in c["cands"] if x["best"]), None)
    rest = [x for x in c["cands"] if x is not best]
    head = ("<b>%s</b> · scan %s · %s · the paper reads bill <b>%s</b>%s %s"
            % (esc(c["supplier"]), esc(c["stamp"]), esc(dmy(c["paper_date"] or c["base"])), esc(c["bill_no"] or "—"),
               (" · " + esc(rs(c["paper_total_p"]))) if c["paper_total_p"] else "",
               "<span class='tag t-ok'>best match found</span>" if best else "<span class='tag t-grey'>no clear match</span>"))
    if best:
        b = best["bill"]
        twice = (" That bill already has its own scan — so this paper was <b>scanned twice</b>." if best.get("scan") else "")
        verdict = ("<div class=verdict>✓ This looks like Marg bill <b>%s</b> (%s, %s): %s.%s</div>"
                   % (esc(b["bill_no"]), esc(dmy(b["bill_date"])), esc(rs(b["amount_p"])),
                      "every line read on the scan agrees in item, batch and rate" if best["n_scan"] else "its number or total agrees", twice))
    elif c["cands"]:
        verdict = "<div class='verdict no'>None of %s's Marg bills from those days clearly matches this scan. Compare them below.</div>" % esc(c["supplier"])
    else:
        verdict = "<div class='verdict no'>%s has no bill in Marg within %d days of this paper's date.</div>" % (esc(c["supplier"]), NEAR_DAYS)
    note = ""
    if again and c.get("answer"):
        note = "<div class=note>%s answered “Amir to enter it in Marg” on %s — it is still not in Marg.</div>" % (esc(c["answer"]["by"]), esc(dmy(c["answer"]["at"])))
    left = ("<div class=col><div class=colh>The scan %s</div><div class=scanf data-src='%s'></div><div class=sub><a target=_blank rel=noopener href='%s'>open in a new tab</a></div>%s</div>"
            % (esc(c["stamp"]), esc(SCAN_URL % c["scan"]), esc(SCAN_URL % c["scan"]), _scan_table(c["lines"])))
    right = _cand_col(best) if best else (_cand_col(rest[0]) if rest else "<div class=col><p class=sub>No Marg bill to compare.</p></div>")
    shown = best or (rest[0] if rest else None)
    others = [x for x in c["cands"] if x is not shown]
    more = ("<details class=more><summary>Other %s bills in Marg from those days (%d)</summary><div class=cols>%s</div></details>"
            % (esc(c["supplier"]), len(others), "".join(_cand_col(x) for x in others))) if others else ""
    btns = []
    for x in ([shown] if shown else []) + others:
        b = x["bill"]
        lab = ("Yes — same bill as %s%s" % (b["bill_no"], " (scanned twice)" if x.get("scan") else "")) if x is best else "It is Marg bill %s (%s)" % (b["bill_no"], dmy(b["bill_date"]))
        btns.append("<button class='b%s' onclick='s849post(this,{scan:%d,answer:\"same\",bill:%d})'>%s</button>"
                    % (" pri" if x is best else "", c["scan"], int(b["id"]), esc(lab)))
    btns.append("<button class=b onclick='s849post(this,{scan:%d,answer:\"enter\"})'>%s</button>"
                % (c["scan"], esc("It is another bill — Amir to enter it in Marg" if c["cands"] else "Not in Marg — Amir to enter it")))
    btns.append("<button class='b ghost' onclick='s849post(this,{scan:%d,answer:\"notbill\"})'>Not a purchase bill</button>" % c["scan"])
    return ("<details class=case%s><summary>%s</summary>%s%s<div class=cols>%s%s</div>%s<div class=btns>%s</div><div class=msg></div></details>"
            % (" open" if open_ else "", head, verdict, note, left, right, more, "".join(btns)))


def page_html(con, args=None):
    head = ('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>Scanned bills not found in Marg</title><style>%s</style></head><body><div class="wrap">'
            '<div class="crumb"><a href="/finance/approvals">Sanjeevni Hub</a> › <b>Scanned bills not found in Marg</b></div>'
            '<h1>Scanned bills not found in Marg</h1>') % CSS
    tail = "<script>var PAGE=%s;</script>%s</div></body></html>" % (json.dumps(PAGE), JS)
    if is_off():
        return head + "<p class=lead>This is switched off just now.</p>" + tail
    v = view(con)
    if not v["ok"]:
        return head + "<p class=lead>The scans could not be read just now. Reload in a minute.</p>" + tail
    lead = ("<p class=lead>Reception scanned these pharmacy bills, and Marg's purchases now run to %s — yet the system cannot find them in Marg. "
            "Open one: the scan, and each Marg bill of that dealer from those days with its own scan and lines, side by side. "
            "Amir sees the same question on his card; the first answer closes it for both.</p>" % esc(dmy(v["reach"])))
    sets = ("<form class=set onsubmit='event.preventDefault();fetch(PAGE+\"/api/setting\",{method:\"POST\",credentials:\"same-origin\",headers:{\"Content-Type\":\"application/json\"},"
            "body:JSON.stringify({days:this.d.value})}).then(function(r){return r.json();}).then(function(j){alert0(j);});'>Ask once Marg's purchases are "
            "<input name=d type=number min=1 max=60 value='%d'> days past the bill's date <button class=b style='padding:3px 10px'>Save</button> <span id=setmsg></span></form>"
            "<script>function alert0(j){var s=document.getElementById('setmsg');s.textContent=j.message||'';s.style.color=j.ok?'#1d7a46':'#b42318';if(j.ok)setTimeout(function(){location.reload();},700);}</script>"
            % v["days"])
    body = []
    if v["asked"]:
        body.append("<h2>Waiting for an answer (%d)</h2>" % len(v["asked"]))
        body += [_case_html(c, open_=(i == 0)) for i, c in enumerate(v["asked"])]
    if v["again"]:
        body.append("<h2>Amir said he would enter it — still not in Marg (%d)</h2>" % len(v["again"]))
        body += [_case_html(c, again=True) for c in v["again"]]
    if not v["asked"] and not v["again"]:
        body.append("<p class=lead><b>Nothing waiting.</b> Every pharmacy scan older than %d days is found in Marg or answered.</p>" % v["days"])
    if v["parked"]:
        body.append("<details class=case><summary><b>Before the counted months</b> — %d scan%s (parked months; yours only)</summary><div style='padding:10px'>%s</div></details>"
                    % (len(v["parked"]), "" if len(v["parked"]) == 1 else "s", "".join(_case_html(c) for c in v["parked"])))
    if v["answered"]:
        rows = []
        for a in v["answered"]:
            what = EN.get(a["answer"], a["answer"])
            if a["answer"] == "same":
                what = what % (a.get("bill_no") or "?")
            undo_b = ("<button class=b style='padding:2px 9px' onclick='fetch(PAGE+\"/api/undo\",{method:\"POST\",credentials:\"same-origin\",headers:{\"Content-Type\":\"application/json\"},"
                      "body:JSON.stringify({id:%d})}).then(function(){location.reload();})'>Undo</button>" % a["id"]) if a["answer"] in ("enter", "notbill") and not a.get("undone_at") else ""
            rows.append("<tr><td>B-%04d</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                int(a["scan"]) % 10000, esc(what), esc(a.get("by_user") or ""), esc(dmy(a.get("at"))) + (" <span class=sub>(undone)</span>" if a.get("undone_at") else ""), undo_b))
        body.append("<details class=case><summary><b>Answered</b> — newest first (%d)</summary><div style='padding:10px'><table><tr><th>Scan</th><th>Answer</th><th>By</th><th>On</th><th></th></tr>%s</table></div></details>"
                    % (len(v["answered"]), "".join(rows)))
    return head + lead + sets + "".join(body) + tail


# ====================================================================== mount
def _mount():
    from flask import Blueprint, jsonify, request            # noqa: PLC0415

    bp = Blueprint("scan_ask", __name__)

    def _doc():
        return _require("checker")

    def _who(u):
        return str((u or {}).get("user") or (u or {}).get("username") or "doctor")

    @bp.route(PAGE)
    def page():
        u, err = _doc()
        if err:
            return err
        return page_html(_db(), request.args), 200, {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store"}

    @bp.route(PAGE + "/api/answer", methods=["POST"])
    def api_answer():
        u, err = _doc()
        if err:
            return err
        b = request.get_json(silent=True) or {}
        try:
            ok, msg = answer(_db(), _who(u), int(b.get("scan") or 0), str(b.get("answer") or ""), int(b.get("bill") or 0) or None, owner=True)
        except Exception as e:                                # noqa: BLE001
            try:
                _db().rollback()
            except Exception:                                 # noqa: BLE001
                pass
            ok, msg = False, "Not recorded (%s)." % e.__class__.__name__
        return jsonify(ok=ok, message=msg), (200 if ok else 409)

    @bp.route(PAGE + "/api/undo", methods=["POST"])
    def api_undo():
        u, err = _doc()
        if err:
            return err
        b = request.get_json(silent=True) or {}
        ok, msg = undo(_db(), _who(u), int(b.get("id") or 0))
        return jsonify(ok=ok, message=msg), (200 if ok else 409)

    @bp.route(PAGE + "/api/setting", methods=["POST"])
    def api_setting():
        u, err = _doc()
        if err:
            return err
        b = request.get_json(silent=True) or {}
        try:
            ok = set_days(_db(), _who(u), int(b.get("days") or 0))
        except (TypeError, ValueError):
            ok = False
        return jsonify(ok=ok, message="Saved." if ok else "Give a number of days from 1 to 60."), (200 if ok else 400)

    @bp.route(PAGE + "/api/healthz")
    def api_healthz():
        return jsonify(ok=True, version=VERSION, off=bool(is_off()))

    return bp


def init(app, db_getter, require_fn):
    """Mount only (called by sanjeevni_approvals.init, fail-soft). Opens no connection."""
    global _db, _require
    _db, _require = db_getter, require_fn
    bp = _mount()
    app.register_blueprint(bp)
    return bp


if __name__ == "__main__":
    # python3 scan_ask.py <finance.db> -- the cases as text (read only, except the CREATE TABLE IF NOT EXISTS of its own table)
    c = sqlite3.connect(sys.argv[1])
    c.row_factory = sqlite3.Row
    v = view(c)
    for k in ("asked", "again", "parked"):
        for x in v[k]:
            best = next((y for y in x["cands"] if y["best"]), None)
            print(k, x["stamp"], x["supplier"], x["bill_no"], x["base"], "best:", best and best["bill"]["bill_no"], [(y["bill"]["bill_no"], y["agree"], y["n_scan"]) for y in x["cands"]])
