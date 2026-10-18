#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s587.py -- kit S587_MORNING_FLOW: the builder. Anchored edits on the LIVE bytes of six files; no new file, no data step.

    python3 -B make_s587.py --finance /root/finance --out DIR

Every file is pinned (FROM md5, the brief's section 1); every anchor must occur exactly once in the live text, else STOP (exit 2, nothing
written). Writes the six files into DIR and prints each md5 -- the installer compares them with PINS.sh.
The brief: claude_code_briefs/S587_MORNING_FLOW.md (v2). D740 (the start-of-day closing), D737 (the morning flow), R2-B2..B5, C6; F-926, F-927,
F-933 (the morning flow), F-936 (the stock-now heading).
"""
import argparse
import hashlib
import os
import sys

FROM = {
    "stock_figure.py": "72b9135ab00db0af2fe8e54091147bb5",
    "shelf_figure.py": "14ef2c24e272ae8ea684615ae82b6cb5",
    "stock_app.py": "1883807d7c0872b805f6101e92206878",
    "amir_day.py": "3deca3b95380165d81ae4a8406a53d75",
    "stock_watch.py": "555202ce50b8df0b5111b5c56952efda",
    "stock_now.html": "ff415eb22ee1ad94a95f2c87365341a3",
}

# =============================================================================================================== stock_figure.py (3.1, 3.2)
SF = []
SF.append(("F1 version, kit, the S587 head note", '''VERSION = "1.1"
KIT = "S583_ARRIVALS_ONE_RULE"                                 # v1.0 was S577_STOCK_ON_SPINE
''', '''VERSION = "1.2"
KIT = "S587_MORNING_FLOW"                                      # v1.1 was S583_ARRIVALS_ONE_RULE, v1.0 S577_STOCK_ON_SPINE
#  v1.2 (S587, 18-Oct-2026, D740 / R2-B2..B5): THE START-OF-DAY CLOSING. A closing printed day D and taken on D between 09:00 and 22:00 (a
#  START capture) may stand for the END of D-1 plus the morning's Marg work -- once verified item by item (verify_start) against the previous
#  verified capture and the spine: the change in the Marg-minus-spine offset per key, the known non-spine Marg work excluded by cause
#  (count vouchers, Amir's 'fix:' taps, the consumption list, purchases dated D, bills first seen after the previous capture); an unexcluded
#  drop no bigger than the day's sales = a sale came before it (set aside); more than count.start_unexplained_max other changes = set aside;
#  else accepted. The verdict is a RECORD (finance.db stock_start_capture, one row per md5, pending -> final once), written lazily by
#  captures() when the context carries a writable connection outside a transaction, and by `python3 stock_figure.py verify-start`. A capture
#  is verified only when the day's sale report is in and the purchase side covers it (purchase_cover) -- never set aside for a short reach.
#  end_day() itself is unchanged (the clock rule). The owner's switch count.start_capture (stock_watch) off = the old rule, nothing written.
#  R2-B3: marg() on a start / early-morning capture never adds the printed day's purchases again (they are inside the capture); such a key is
#  approx (reason purchase_on_start), as is a verification-excluded key with a sale dated D (start_excluded) and an unexplained key
#  (start_unexplained). The S577 early-morning helper is folded into this. R2-B4: purchase_cover() -- the spine's purchase reach (a), the newest purchase
#  exports after the closing (b), or VISIT COVER (c): the last purchase export after Amir's last bill-entry tap of the visit covers every
#  closing until his next visit's bill entry. tryable() takes it for its purchase half (both callers pass con / ctx).
''' ))
SF.append(("F2a reach(): the newest purchase export of each family, whatever its date_to (clause b)", '''    ls, lb, li = last(S), last(B), last(I)
    lp = min(lb, li) if (lb and li) else ""
    return dict(last_sale=ls, sale_stamp=stamp_of(S, ls), last_pur=lp, pur_stamp=(min(stamp_of(B, lb), stamp_of(I, li)) if lp else ""))
''', '''    ls, lb, li = last(S), last(B), last(I)
    lp = min(lb, li) if (lb and li) else ""

    def newest(fam_sql):                                      # S587 (purchase_cover b): the newest export of a family, whatever day it reaches
        return str(sp.q("SELECT MAX(stamp) AS s FROM sp_export WHERE ok=1 AND " + fam_sql)[0]["s"] or "")
    nb, ni = newest(B), newest(I)
    return dict(last_sale=ls, sale_stamp=stamp_of(S, ls), last_pur=lp, pur_stamp=(min(stamp_of(B, lb), stamp_of(I, li)) if lp else ""),
                pur_newest=(min(nb, ni) if (nb and ni) else ""))
'''))
SF.append(("F2 tryable: the purchase half is purchase_cover; sale_landed, _ts, visit cover", '''def tryable(c, reach_):
    """(ok, short) -- a closing is tried only when the spine's reach covers it (R1-B2): last_sale and last_pur at or past its end_day, and
    both newest exports cover it (covers: captured after it, or standing by their own capture for the end of a day at or after its
    end_day -- S570, F-905). short names what is missing: 'sale' | 'pur' | ''."""
    d = c.get("end_day") or ""
    if not d or not reach_:
        return False, "sale"
    if reach_["last_sale"] < d or not covers(reach_["last_sale"], reach_["sale_stamp"], c, d):
        return False, "sale"
    if not reach_["last_pur"] or reach_["last_pur"] < d or not covers(reach_["last_pur"], reach_["pur_stamp"], c, d):
        return False, "pur"
    return True, ""
''', '''def tryable(c, reach_, con=None, ctx=None):
    """(ok, short) -- a closing is tried only when the spine's reach covers it (R1-B2): the SALE half as before (last_sale at or past its
    end_day and the newest sale export covering it -- S570, F-905); the PURCHASE half is purchase_cover() (S587, R2-B4: the reach, the newest
    exports after the closing, or Amir's visit cover -- the last needs `con`; with con None only the first two run). `c` is read with .get
    (stock_app passes a bare dict). short names what is missing: 'sale' | 'pur' | ''."""
    d = c.get("end_day") or ""
    if not d or not reach_:
        return False, "sale"
    if reach_["last_sale"] < d or not covers(reach_["last_sale"], reach_["sale_stamp"], c, d):
        return False, "sale"
    sp = ctx.sp if (ctx is not None and ctx.sp is not None) else None
    if not purchase_cover(con, sp, c, reach_, ctx):
        return False, "pur"
    return True, ""


def _ts(s):
    """Any stored moment -> 'YYYY-MM-DD HH:MM:SS' so stamps of different writers compare as text (charter 11; amir_day._norm_ts's rule):
    Marg's YYYYMMDD-HHMMSS, ISO with a 'T' and a zone, or a space. None when it is not a moment."""
    if not s:
        return None
    s = str(s).strip()
    if re.match(r"^\\d{8}-\\d{6}$", s):
        return "%s-%s-%s %s:%s:%s" % (s[0:4], s[4:6], s[6:8], s[9:11], s[11:13], s[13:15])
    s = s.replace("T", " ")
    if len(s) >= 19:
        return s[:19]
    if len(s) == 16:
        return s + ":00"
    if len(s) == 10:
        return s + " 00:00:00"
    return None


def purchase_cover(con, sp, c, reach_, ctx=None):
    """S587 (R2-B4): True when the PURCHASE side covers closing `c` (end_day d) by any of
      (a) the spine's purchase reach: last_pur at or past d and its newest exports covering the closing (covers: as before);
      (b) the newest purchase export of EACH family (sp_export ok=1) is stamped after the closing;
      (c) visit cover (visit_cover): the last purchase export after Amir's last bill-entry tap of the visit, with no 'self' answer and no
          open self-wait after it, covers every closing after it until his next visit's bill entry (needs `con`; None -> not by this clause).
    `c` is read with .get (stock_app's bare dict). purchase_cover_how() names the clause."""
    return purchase_cover_how(con, sp, c, reach_, ctx) is not None


def purchase_cover_how(con, sp, c, reach_, ctx=None):
    """'a' | 'b' | dict(clause='c', ...) | None -- which clause of purchase_cover covers the closing (the walk and the report print it)."""
    d = str((c or {}).get("end_day") or "")[:10]
    if not d:
        return None
    if reach_:
        lp = str(reach_.get("last_pur") or "")
        if lp and lp >= d and covers(lp, str(reach_.get("pur_stamp") or ""), c, d):
            return "a"
    newest = str((reach_ or {}).get("pur_newest") or "")      # reach() carries it; a bare reach dict without it: read the spine
    if not newest and sp is not None and getattr(sp, "ok", False):
        try:
            b = str((sp.q("SELECT MAX(stamp) AS s FROM sp_export WHERE ok=1 AND family='PURCHASE_BILLWISE'") or [{"s": ""}])[0]["s"] or "")
            i = str((sp.q("SELECT MAX(stamp) AS s FROM sp_export WHERE ok=1 AND family IN ('PURCHASE_ITEMWISE','PURCHASE_BILLITEMWISE')") or [{"s": ""}])[0]["s"] or "")
            newest = min(b, i) if (b and i) else ""
        except sqlite3.Error:
            newest = ""
    if newest and newest > str(c.get("stamp") or ""):
        return "b"
    if con is None and (ctx is None or ctx.con is None):
        return None
    v = visit_cover(con if con is not None else ctx.con, c, ctx)
    return v if v else None


def _visit_facts(con, ctx):
    """Read once per Ctx (finance.db, small tables): Amir's visit days (amir_day) with their opened_at, his step-2 ('Sab bill daal diye') taps by
    day (amir_step_log), every purchase export (purchase_export: family, Marg's stamp, rows, amount), his 'self' answers' moments and the
    open self-waits. Every moment through _ts."""
    if "visit" in ctx.c:
        return ctx.c["visit"]
    F = dict(days=[], opened={}, t2={}, exports=[], selfs=[], waits=[])
    if con is not None:
        try:
            if _has(con, "amir_day"):
                for day, opened in con.execute("SELECT day, opened_at FROM amir_day ORDER BY day"):
                    F["days"].append(str(day)[:10])
                    F["opened"][str(day)[:10]] = _ts(opened)
            if _has(con, "amir_step_log"):
                for day, at in con.execute("SELECT day, done_at FROM amir_step_log WHERE step=2 ORDER BY done_at"):
                    t = _ts(at)
                    if t:
                        F["t2"].setdefault(str(day)[:10], []).append(t)
            if _has(con, "purchase_export"):
                for typ, es, rec, n, amt in con.execute("SELECT type, export_stamp, received_at, n_rows, grand_amount_p FROM purchase_export "
                                                        "WHERE type IN ('BILLWISE','ITEMWISE','BILLITEMWISE')"):
                    at = _ts(es) or _ts(rec)
                    if at:
                        F["exports"].append(dict(fam=("B" if typ == "BILLWISE" else "I"), at=at, n=n, amt=amt, type=typ))
            if _has(con, "amir_bill_answer"):
                F["selfs"] = [t for t in (_ts(r[0]) for r in con.execute("SELECT at FROM amir_bill_answer WHERE reason='self'")) if t]
            if _has(con, "amir_self_wait"):
                F["waits"] = [t for t in (_ts(r[0]) for r in con.execute("SELECT marked_at FROM amir_self_wait WHERE cleared_at IS NULL")) if t]
        except sqlite3.Error:
            pass
    ctx.c["visit"] = F
    return F


def visit_cover(con, c, ctx=None):
    """S587 (R2-B4, restated after R1-B2 / R1-B3): clause (c). V = Amir's visit day (amir_day.day) on or before the closing's calendar day.
    T2 = his LAST step-2 tap on V before the closing (re-taps after the close included). E = the newest purchase export of EACH family (anyone's
    -- purchase_export rows; an export identical in rows and amount to the visit's own continues it) stamped at or after T2 and before the
    closing; E covers the closing when no 'self' answer and no open self-wait fall between E and the closing. On V itself the same clause runs
    on the taps made so far (R1-B3). A closing on V BEFORE he opened his day or tapped bill entry is judged by the previous visit's cover (the
    bound: the next visit's first step-2 tap, or its opened_at -- bills he keys before his first tap are never covered falsely). A visit day
    with no step-2 tap gives no cover. Returns dict(clause='c', visit, t2, at, identical) or None."""
    ctx = _ctx(con, None, ctx)
    cs = _ts(c.get("stamp_iso") or stamp_iso(c.get("stamp")))
    if not cs:
        return None
    F = _visit_facts(ctx.con, ctx)
    days = [d for d in F["days"] if d <= cs[:10]]
    if not days:
        return None
    V = days[-1]
    if V == cs[:10]:
        taps = [t for t in F["t2"].get(V, []) if t < cs]
        if not taps:
            first = min([t for t in F["t2"].get(V, [])] + ([F["opened"][V]] if F["opened"].get(V) else [])) if (F["t2"].get(V) or F["opened"].get(V)) else V + " 00:00:00"
            if cs >= first or len(days) < 2:
                return None
            V = days[-2]
            taps = list(F["t2"].get(V, []))
    else:
        taps = list(F["t2"].get(V, []))
    if not taps:
        return None
    t2 = max(taps)
    E = {}
    for fam in ("B", "I"):
        cand = [e for e in F["exports"] if e["fam"] == fam and t2 <= e["at"] < cs]
        if not cand:
            return None
        E[fam] = max(cand, key=lambda e: e["at"])
    at = max(E["B"]["at"], E["I"]["at"])
    if any(at < s <= cs for s in F["selfs"]) or any(at < w <= cs for w in F["waits"]):
        return None
    own = {fam: [e for e in F["exports"] if e["fam"] == fam and e["at"][:10] == V and e["at"] < t2] for fam in ("B", "I")}
    ident = all(own[fam] and (E[fam]["n"], E[fam]["amt"]) == (max(own[fam], key=lambda e: e["at"])["n"], max(own[fam], key=lambda e: e["at"])["amt"]) for fam in ("B", "I"))
    return dict(clause="c", visit=V, t2=t2, at=at, identical=bool(ident and at[:10] != V))


def sale_landed(sp, day):
    """The day (ISO) the sale report reaching `day` was taken -- the earliest ok=1 SALE_BILLWISE export with date_to >= day; '' when none."""
    try:
        r = sp.q("SELECT MIN(stamp) AS s FROM sp_export WHERE ok=1 AND family='SALE_BILLWISE' AND date_to>=?", str(day)[:10])
        return stamp_iso((r[0]["s"] if r else "") or "")[:10]
    except sqlite3.Error:
        return ""
'''))
SF.append(("F3 captures(): the start captures, their verdicts", '''def captures(sp, ctx=None):
    """Every closing capture held by name (sp_close_name's md5s) with its export's printed day and stamp (sp_export.as_on / stamp -- the
    one copy, R2-C17), stamp_iso and end_day. Oldest stamp first. usable = end_day is not None."""
    ctx = _ctx(None, sp, ctx)
    if "caps" in ctx.c:
        return ctx.c["caps"]
    out = []
    if ready(sp):
        for r in sp.q("SELECT e.md5 AS md5, e.as_on AS as_on, e.stamp AS stamp FROM sp_export e WHERE e.md5 IN (SELECT DISTINCT md5 FROM sp_close_name) "
                      "ORDER BY e.stamp, e.md5"):
            si = stamp_iso(r["stamp"])
            e = end_day(str(r["as_on"] or ""), si) if si else None
            out.append(dict(md5=str(r["md5"]), as_on=str(r["as_on"] or ""), stamp=str(r["stamp"] or ""), stamp_iso=si, end_day=e, usable=e is not None))
    ctx.c["caps"] = out
    return out
''', '''def captures(sp, ctx=None):
    """Every closing capture held by name (sp_close_name's md5s) with its export's printed day and stamp (sp_export.as_on / stamp -- the
    one copy, R2-C17), stamp_iso and end_day. Oldest stamp first. usable = end_day is not None.
    S587 (D740): a same-day print between 09:00 and 22:00 is a START capture (start=True, start_day=D-1): usable, with end_day=D-1, only
    once its verdict is 'accepted' (stock_start_capture, finance.db -- read through ctx.con; judged here lazily when that connection may
    write, see _start_apply); otherwise unusable as before. A same-day print before 09:00 is marked early=True (end_day D-1 as before).
    verdict: None (not a start capture) | 'pending' | 'accepted' | 'set_aside' | 'off' (the owner's switch count.start_capture is off)."""
    ctx = _ctx(None, sp, ctx)
    if "caps" in ctx.c:
        return ctx.c["caps"]
    out = []
    if ready(sp):
        for r in sp.q("SELECT e.md5 AS md5, e.as_on AS as_on, e.stamp AS stamp FROM sp_export e WHERE e.md5 IN (SELECT DISTINCT md5 FROM sp_close_name) "
                      "ORDER BY e.stamp, e.md5"):
            si = stamp_iso(r["stamp"])
            as_on = str(r["as_on"] or "")
            e = end_day(as_on, si) if si else None
            c = dict(md5=str(r["md5"]), as_on=as_on, stamp=str(r["stamp"] or ""), stamp_iso=si, end_day=e, usable=e is not None,
                     start=False, early=False, start_day=None, verdict=None)
            if si and len(as_on) == 10 and as_on == si[:10]:
                hm = si[11:16]
                if hm < "09:00":
                    c["early"] = True
                elif hm < "22:00":
                    c["start"], c["start_day"] = True, _day_before(as_on)
            out.append(c)
        try:
            _start_apply(out, ctx)
        except Exception as ex:                                # noqa: BLE001 -- fail-soft: every start capture stays unusable, one line
            print("stock_figure: start captures not judged: %s" % str(ex)[:160], file=sys.stderr)
    ctx.c["caps"] = out
    return out


def _day_before(d):
    try:
        return (dt.date.fromisoformat(str(d)[:10]) - dt.timedelta(days=1)).isoformat()
    except ValueError:
        return None


def capture_of(sp, md5, ctx=None):
    """The capture dict of one md5 (captures()), or None."""
    ctx = _ctx(None, sp, ctx)
    if "capmap" not in ctx.c:
        ctx.c["capmap"] = {c["md5"]: c for c in captures(sp, ctx)}
    return ctx.c["capmap"].get(str(md5 or ""))
'''))
SF.append(("F4 the start-capture record and its verdict, after _cn_rows", '''# ------------------------------------------------------------------ identity (charter 12)
def _k_by_name(sp, ctx):''', '''# ------------------------------------------------------------------ the start-of-day closing (S587, D740; R2-B2) -- the verdict record
START_DDL = ("CREATE TABLE IF NOT EXISTS stock_start_capture (md5 TEXT PRIMARY KEY, as_on TEXT, stamp_iso TEXT, end_day TEXT, "
             "verdict TEXT NOT NULL, reason TEXT, checked_at TEXT, built TEXT, prev_md5 TEXT, n_keys INTEGER, n_excluded INTEGER, "
             "n_unexplained INTEGER, detail TEXT)")              # one row per capture md5; pending -> a final verdict once (a record, never re-judged)
START_FINAL = ("accepted", "set_aside")


def _ensure_start(con):
    con.execute(START_DDL)


def _start_settings(con, ctx):
    """(count.start_capture on?, count.start_unexplained_max) through stock_watch.settings -- the one settings reader -- read once per Ctx;
    the defaults (on, 3) when it cannot be read."""
    if "startset" not in ctx.c:
        on, mx = True, 3
        try:
            S = _sw().settings(con)
            on = bool(S.get("start_capture", True))
            mx = int(S.get("start_unexplained_max", 3))
        except Exception:                                     # noqa: BLE001
            pass
        ctx.c["startset"] = (on, max(0, mx))
    return ctx.c["startset"]


def _start_rows(con, ctx):
    """{md5: row dict} -- every stock_start_capture row (read once per Ctx; {} with no connection or no table)."""
    if "startrows" not in ctx.c:
        rows = {}
        if con is not None and _has(con, "stock_start_capture"):
            try:
                for r in con.execute("SELECT md5, as_on, stamp_iso, end_day, verdict, reason, checked_at, built, prev_md5, n_keys, n_excluded, n_unexplained, detail "
                                     "FROM stock_start_capture"):
                    rows[str(r[0])] = dict(md5=str(r[0]), as_on=r[1], stamp_iso=r[2], end_day=r[3], verdict=str(r[4] or "pending"), reason=r[5] or "",
                                           checked_at=r[6], built=r[7], prev_md5=r[8], n_keys=r[9], n_excluded=r[10], n_unexplained=r[11], detail=r[12])
            except sqlite3.Error:
                rows = {}
        ctx.c["startrows"] = rows
    return ctx.c["startrows"]


def _may_write(con):
    """A connection that may take the verdict's write: present and not inside the caller's own transaction (its pending writes are never
    committed by this module). A read-only connection raises on the write and the capture stays pending (fail-soft, one stderr line)."""
    try:
        return con is not None and not con.in_transaction
    except Exception:                                         # noqa: BLE001
        return False


def _start_apply(caps, ctx):
    """For every START capture, in stamp order: the switch; the recorded verdict (or, when the context's connection may write and the capture
    is within LATE_DAYS with no final verdict yet, the verdict judged now and written); accepted -> usable with end_day = D-1."""
    starts = [c for c in caps if c["start"]]
    if not starts:
        return
    con = ctx.con
    on, mx = _start_settings(con, ctx)
    if not on:
        for c in starts:
            c["verdict"] = "off"
        return
    rows = _start_rows(con, ctx)
    recent = (today() - dt.timedelta(days=LATE_DAYS)).isoformat()
    for c in starts:
        v = rows.get(c["md5"])
        if (v is None or v["verdict"] not in START_FINAL) and c["as_on"] >= recent and _may_write(con):
            nv = _judge_start(con, ctx.sp, c, caps, ctx, mx, v)
            if nv is not None:
                v = nv
                rows[c["md5"]] = v
        c["verdict"] = (v or {}).get("verdict") or "pending"
        if c["verdict"] == "accepted":
            c["end_day"], c["usable"] = c["start_day"], True


def _judge_start(con, sp, S, caps, ctx, mx, old):
    """start_ready -> verify_start -> the row written (INSERT when none; UPDATE while pending). Returns the row, or None when it could not be
    judged or written (the capture stays as it was)."""
    try:
        _ensure_start(con)
        ready_, why = start_ready(con, sp, S, ctx)
        if ready_:
            row = verify_start(con, sp, S, caps, ctx, mx)
        else:
            row = dict(verdict="pending", reason=why, prev_md5=None, n_keys=None, n_excluded=None, n_unexplained=None, detail={})
        row.update(md5=S["md5"], as_on=S["as_on"], stamp_iso=S["stamp_iso"], end_day=S["start_day"], checked_at=dt.datetime.now().replace(microsecond=0).isoformat(),
                   built=_built(sp))
        det = json.dumps(row.get("detail") or {}, ensure_ascii=False, sort_keys=True, default=str)
        if old is None:
            con.execute("INSERT OR IGNORE INTO stock_start_capture (md5, as_on, stamp_iso, end_day, verdict, reason, checked_at, built, prev_md5, n_keys, n_excluded, "
                        "n_unexplained, detail) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (row["md5"], row["as_on"], row["stamp_iso"], row["end_day"], row["verdict"], row["reason"], row["checked_at"], row["built"], row["prev_md5"],
                         row["n_keys"], row["n_excluded"], row["n_unexplained"], det))
        else:
            con.execute("UPDATE stock_start_capture SET verdict=?, reason=?, checked_at=?, built=?, prev_md5=?, n_keys=?, n_excluded=?, n_unexplained=?, detail=? "
                        "WHERE md5=? AND verdict NOT IN ('accepted','set_aside')",
                        (row["verdict"], row["reason"], row["checked_at"], row["built"], row["prev_md5"], row["n_keys"], row["n_excluded"], row["n_unexplained"], det, row["md5"]))
        con.commit()
        row["detail"] = det
        return row
    except Exception as ex:                                   # noqa: BLE001
        try:
            con.rollback()
        except Exception:                                     # noqa: BLE001
            pass
        print("stock_figure: start capture %s (%s) stays pending: %s" % (S["md5"][:8], S["stamp_iso"], str(ex)[:160]), file=sys.stderr)
        return None


def _built(sp):
    try:
        return str((sp.q("SELECT value FROM sp_meta WHERE key='built'") or [{"value": ""}])[0]["value"] or "")
    except Exception:                                         # noqa: BLE001
        return ""


def start_ready(con, sp, S, ctx=None):
    """(ready, why) -- a start capture printed D can be judged once the spine's sale reach has D (the day's sale report is in: the next
    morning at the earliest -- a start capture is never used on its own day) AND the purchase side covers it (purchase_cover on the closing
    as it would stand, end_day D-1). why: 'sale_short' | 'pur_short' | ''. Never set aside for a short reach (R2-B2)."""
    ctx = _ctx(con, sp, ctx)
    R = _reach_once(sp, ctx)
    if not R or str(R.get("last_sale") or "") < str(S["as_on"]):
        return False, "sale_short"
    c = dict(S, end_day=S["start_day"])
    if not purchase_cover(ctx.con, sp, c, R, ctx):
        return False, "pur_short"
    return True, ""


def _bal(sp, d, ctx):
    """{k20: the spine's own stock at the end of day d} = SUM(sp_move.units) with date <= d, OPENING included. Once per (Ctx, d)."""
    ck = ("bal", str(d)[:10])
    if ck not in ctx.c:
        ctx.c[ck] = {str(r["k"]): float(r["u"] or 0) for r in sp.q("SELECT k20 AS k, SUM(units) AS u FROM sp_move WHERE date<=? GROUP BY k20", str(d)[:10]) if r["k"]}
    return ctx.c[ck]


def _sales_on(sp, d, ctx):
    """{k20: |units sold| on day d} (SALE units are negative in sp_move -- the absolute sum). Once per (Ctx, d)."""
    ck = ("salesD", str(d)[:10])
    if ck not in ctx.c:
        ctx.c[ck] = {str(r["k"]): abs(float(r["u"] or 0)) for r in sp.q("SELECT k20 AS k, SUM(units) AS u FROM sp_move WHERE kind='SALE' AND date=? GROUP BY k20", str(d)[:10]) if r["k"]}
    return ctx.c[ck]


def _purchases_on(sp, d, ctx):
    """{k20: (rows, signed units)} of PURCHASE / PURCHASE_RETURN dated d. Once per (Ctx, d)."""
    ck = ("purD", str(d)[:10])
    if ck not in ctx.c:
        ctx.c[ck] = {str(r["k"]): (int(r["n"] or 0), float(r["u"] or 0)) for r in
                     sp.q("SELECT k20 AS k, COUNT(*) AS n, SUM(units) AS u FROM sp_move WHERE kind IN ('PURCHASE','PURCHASE_RETURN') AND date=? GROUP BY k20", str(d)[:10]) if r["k"]}
    return ctx.c[ck]


def _units_by_key(sp, md5, ctx):
    """{k20: units} of one capture (the '' key dropped) and {k20: its first printed name}."""
    by_k = _cn_rows(sp, md5, ctx)[1]
    return ({k: float(sum(u for (_n, _p, u) in rows)) for k, rows in by_k.items() if k},
            {k: rows[0][0] for k, rows in by_k.items() if k and rows})


def _start_excluded(con, sp, S, P, ctx):
    """{cause: set(k20)} -- the keys with KNOWN non-spine Marg work between the previous verified capture P and the start capture S:
      vouchers  count-voucher batches first entered in (P.stamp, S.stamp] (stock_voucher_entered's first non-empty row of a batch entered now,
                the rule of stock_app._s446_window; its lines, not voided, through key_of);
      fix       amir_job 'fix:%' rows with done_at in the window (his 'Aaj ke item theek kar diye' tap, or seen in Marg);
      consume   the owner's consumption list (loss_piles.settings: stock.consume_items), through key_of;
      purchase  keys with a PURCHASE / PURCHASE_RETURN dated the printed day D in sp_move (inside the capture when entered before it);
      bill_new  keys of a purchase bill first seen (purchase_bill.first_seen_day) on or after P's own day (a bill first seen on P's day is
                undecidable: excluded too), its lines found in sp_purchase_line by supplier key, bill number and date."""
    lo, hi = _ts(P["stamp_iso"]), _ts(S["stamp_iso"])
    D = S["as_on"]
    out = dict(vouchers=set(), fix=set(), consume=set(), purchase=set(), bill_new=set())
    con = ctx.con if ctx.con is not None else con
    if con is None:
        out["purchase"] = set(_purchases_on(sp, D, ctx))
        return out
    try:
        if _has(con, "stock_voucher_entered") and _has(con, "stock_voucher_line"):
            ent, first = {}, {}
            for cid, rno, kind, bno, vno, at in con.execute("SELECT count_id, round_no, kind, batch_no, marg_voucher_no, at FROM stock_voucher_entered ORDER BY id"):
                k = (cid, rno, kind, bno)
                if str(vno or "").strip():
                    ent[k] = True
                    first.setdefault(k, _ts(at))
                else:
                    ent.pop(k, None)
            win = {k for k in ent if first.get(k) and lo < first[k] <= hi}
            if win:
                vf = (" AND NOT EXISTS (SELECT 1 FROM stock_voucher_void v WHERE v.count_id=l.count_id AND v.round_no=l.round_no AND v.kind=l.kind AND v.batch_no=l.batch_no)"
                      if _has(con, "stock_voucher_void") else "")
                for cid, rno, kind, bno, item in con.execute("SELECT count_id, round_no, kind, batch_no, item FROM stock_voucher_line l WHERE 1=1" + vf):
                    if (cid, rno, kind, bno) in win:
                        out["vouchers"].add(key_of(sp, item, ctx))
    except sqlite3.Error:
        pass
    try:
        if _has(con, "amir_job"):
            for subj, at in con.execute("SELECT subject, done_at FROM amir_job WHERE key LIKE 'fix:%' AND done_at IS NOT NULL"):
                t = _ts(at)
                if t and lo < t <= hi:
                    out["fix"].add(key_of(sp, subj, ctx))
    except sqlite3.Error:
        pass
    try:
        import loss_piles                                     # noqa: PLC0415 -- beside this file; stdlib only at module level
        for nm in loss_piles.settings(con).get("consume_items") or []:
            out["consume"].add(key_of(sp, nm, ctx))
    except Exception:                                         # noqa: BLE001
        pass
    out["purchase"] = set(_purchases_on(sp, D, ctx))
    try:
        if _has(con, "purchase_bill"):
            pl = {}
            for r in sp.q("SELECT supkey, bill, date, k20 FROM sp_purchase_line"):
                pl.setdefault((str(r["supkey"] or ""), _bill(r["bill"]), str(r["date"] or "")[:10]), set()).add(str(r["k20"] or ""))
            sk = _sw().supkey
            for sn, sup, bno, bdt in con.execute("SELECT supplier_norm, supplier, bill_no, bill_date FROM purchase_bill WHERE first_seen_day >= ?", (lo[:10],)):
                for key in {(sk(sn), _bill(bno), str(bdt or "")[:10]), (sk(sup), _bill(bno), str(bdt or "")[:10])}:
                    out["bill_new"] |= {k for k in pl.get(key, set()) if k}
    except sqlite3.Error:
        pass
    return out


def verify_start(con, sp, S, caps, ctx=None, mx=3):
    """R2-B2, the one test: P = the newest usable capture (accepted or clean) with end_day <= D-1 and stamp < S.stamp (none -> pending,
    no_prev). For every key of S or P: change = (units_S - bal(D-1)) - (units_P - bal(P.end_day)) -- the change in the Marg-minus-spine
    offset, never an absolute compare. The excluded keys (_start_excluded) are set apart by cause. An unexcluded key with change < 0 and
    |change| <= its sales dated D -> set_aside 'sale_before'; more than `mx` other unexcluded keys with |change| >= 0.5 -> set_aside
    'unexplained'; else accepted (those keys listed: approx on this capture). Returns the row (verdict, reason, prev_md5, n_*, detail)."""
    ctx = _ctx(con, sp, ctx)
    D, d1 = S["as_on"], S["start_day"]
    prev = [c for c in caps if c["usable"] and c["end_day"] and c["end_day"] <= d1 and c["stamp"] < S["stamp"] and c["md5"] != S["md5"]]
    if not prev:
        return dict(verdict="pending", reason="no_prev", prev_md5=None, n_keys=None, n_excluded=None, n_unexplained=None, detail={})
    P = max(prev, key=lambda c: c["stamp"])
    uS, nS = _units_by_key(sp, S["md5"], ctx)
    uP, nP = _units_by_key(sp, P["md5"], ctx)
    names = dict(nP)
    names.update(nS)
    bS, bP = _bal(sp, d1, ctx), _bal(sp, P["end_day"], ctx)
    salesD = _sales_on(sp, D, ctx)
    keys = sorted(set(uS) | set(uP))
    change = {k: (uS.get(k, 0.0) - bS.get(k, 0.0)) - (uP.get(k, 0.0) - bP.get(k, 0.0)) for k in keys}
    exc = _start_excluded(con, sp, S, P, ctx)
    excl = set().union(*exc.values()) if exc else set()
    sale_before, unexpl = [], []
    for k in keys:
        if k in excl:
            continue
        ch = change[k]
        if abs(ch) < 0.5:
            continue
        if ch < 0 and salesD.get(k, 0.0) > 0 and abs(ch) <= salesD[k] + 1e-9:
            sale_before.append((k, names.get(k, k), round(ch, 2), salesD[k]))
        else:
            unexpl.append((k, names.get(k, k), round(ch, 2)))
    if sale_before:
        verdict, reason = "set_aside", "sale_before"
    elif len(unexpl) > int(mx):
        verdict, reason = "set_aside", "unexplained"
    else:
        verdict, reason = "accepted", ""
    detail = dict(prev=dict(md5=P["md5"], as_on=P["as_on"], stamp_iso=P["stamp_iso"], end_day=P["end_day"], start=bool(P.get("start"))),
                  max_unexplained=int(mx), sale_before=sale_before, unexplained=unexpl,
                  excluded={cause: sorted((k, names.get(k, k)) for k in ks if k in change) for cause, ks in exc.items()},
                  changed_excluded=sorted((k, names.get(k, k), round(change[k], 2)) for k in excl if k in change and abs(change[k]) >= 0.5))
    return dict(verdict=verdict, reason=reason, prev_md5=P["md5"], n_keys=len(keys), n_excluded=len(excl & set(keys)), n_unexplained=len(unexpl), detail=detail)


def start_marks(con, sp, cap, ctx=None):
    """{k20: reason} -- the keys of a START / EARLY capture whose figure is approximate (R2-B3, §3.1): 'purchase_on_start' for a key with a
    PURCHASE / PURCHASE_RETURN dated the printed day (inside the capture when entered before it; never added again by marg()); on an accepted
    start capture also 'start_unexplained' (the verdict's unexplained keys) and 'start_excluded' (a verification-excluded key with a sale dated
    D -- its D-sale cannot be told from the capture's). {} for an ordinary capture. Once per (Ctx, md5)."""
    ctx = _ctx(con, sp, ctx)
    if not cap or not (cap.get("start") or cap.get("early")):
        return {}
    ck = ("smarks", cap["md5"])
    if ck in ctx.c:
        return ctx.c[ck]
    out = {k: "purchase_on_start" for k in _purchases_on(sp, cap["as_on"], ctx)}
    if cap.get("start"):
        row = _start_rows(ctx.con, ctx).get(cap["md5"])
        try:
            d = json.loads((row or {}).get("detail") or "{}") if row else {}
        except ValueError:
            d = {}
        for x in d.get("unexplained") or []:
            out.setdefault(str(x[0]), "start_unexplained")
        salesD = _sales_on(sp, cap["as_on"], ctx)
        for _cause, ks in (d.get("excluded") or {}).items():
            for x in ks:
                if str(x[0]) in salesD:
                    out.setdefault(str(x[0]), "start_excluded")
    ctx.c[ck] = out
    return out


def morning_skip_keys(sp, cap, ctx=None):
    """start_marks for the proof table (stock_app._s524_table): {k20: reason} of a capture dict, {} for None."""
    ctx = _ctx(None, sp, ctx)
    return start_marks(ctx.con, sp, cap, ctx) if cap else {}


def _prev_capture(sp, c, ctx):
    """The usable capture standing for the newest end_day BEFORE c's (record_gaps' P -- the base of a between-two-closings judgment)."""
    earlier = [x["end_day"] for x in usable_captures(sp, ctx) if x["end_day"] and c.get("end_day") and x["end_day"] < c["end_day"]]
    return capture_for(sp, max(earlier), ctx) if earlier else None


def start_report(con, sp, ctx=None, days=7):
    """[dict] -- every start capture of the last `days` days with its verdict, reason, the deciding keys and the excluded keys by cause
    (`python3 stock_figure.py verify-start`, the installer's state step, the walk)."""
    ctx = _ctx(con, sp, ctx)
    lo = (today() - dt.timedelta(days=days)).isoformat()
    out = []
    rows = _start_rows(ctx.con, ctx)
    for c in captures(sp, ctx):
        if not c["start"] or c["as_on"] < lo:
            continue
        r = rows.get(c["md5"]) or {}
        try:
            d = json.loads(r.get("detail") or "{}") if r else {}
        except ValueError:
            d = {}
        out.append(dict(md5=c["md5"][:8], as_on=c["as_on"], stamp_iso=c["stamp_iso"], start_day=c["start_day"], verdict=c["verdict"], reason=r.get("reason") or "",
                        usable=c["usable"], n_keys=r.get("n_keys"), n_excluded=r.get("n_excluded"), n_unexplained=r.get("n_unexplained"),
                        prev=(d.get("prev") or {}), sale_before=d.get("sale_before") or [], unexplained=d.get("unexplained") or [],
                        excluded={k: len(v) for k, v in (d.get("excluded") or {}).items()}, changed_excluded=d.get("changed_excluded") or []))
    return out


# ------------------------------------------------------------------ identity (charter 12)
def _k_by_name(sp, ctx):'''))
SF.append(("F5 marg(): the printed day's purchases are inside a start / early capture (R2-B3)", '''def marg(con, sp, name, at=None, ctx=None):
    """Marg's figure at `at` (today): closing().units + sp_move of key_of(name) over (end_day, at] (MOVE_KINDS). approx=True whenever
    family() has more than one member, whatever `by` is. taps = tapped arrivals the spine does not carry, beside the figure."""
    ctx = _ctx(con, sp, ctx)
    c = closing(con, sp, name, at, ctx)
    if c is None:
        return None
    a = _iso(at)
    k = key_of(sp, name, ctx)
    fam = family(sp, k, c["md5"], ctx)
    sold, ret, bought = moves(sp, k, c["end_day"], a, incl_from=False)
    net = spine_move(sp, k, c["end_day"], a)
    return dict(figure=float(c["units"]) + net, closing=c, sold=sold, returned=ret, bought=bought, upto=a, key=k,
                approx=bool(c["approx"] or len(fam) > 1), family=fam, taps=taps(con, sp, name, c["stamp_iso"], ctx))
''', '''def marg(con, sp, name, at=None, ctx=None):
    """Marg's figure at `at` (today): closing().units + sp_move of key_of(name) over (end_day, at] (MOVE_KINDS). approx=True whenever
    family() has more than one member, whatever `by` is. taps = tapped arrivals the spine does not carry, beside the figure.
    S587 (R2-B3): on a START or EARLY-morning capture (printed D, standing for the end of D-1) the purchases dated D are already inside the
    capture -- they are never added again (only D's sales, returns and reconciliations, and every kind after D), and such a key is approx with
    approx_reason 'purchase_on_start' (also at `at` == end_day); an accepted start capture's unexplained keys ('start_unexplained') and its
    verification-excluded keys with a sale dated D ('start_excluded') are approx too (start_marks). When the figure is asked exactly at the
    capture's end day (a judgment between two closings: shelf_figure.record_gaps) and the PREVIOUS end day's capture is a morning one holding
    a purchase of its printed day for this key, the key is approx as well -- the base side of R2-B3."""
    ctx = _ctx(con, sp, ctx)
    c = closing(con, sp, name, at, ctx)
    if c is None:
        return None
    a = _iso(at)
    k = key_of(sp, name, ctx)
    fam = family(sp, k, c["md5"], ctx)
    sold, ret, bought = moves(sp, k, c["end_day"], a, incl_from=False)
    net = spine_move(sp, k, c["end_day"], a)
    cap = capture_of(sp, c["md5"], ctx)
    reason = None
    if cap and (cap["start"] or cap["early"]):
        reason = start_marks(ctx.con, sp, cap, ctx).get(k)
        pD = _purchases_on(sp, cap["as_on"], ctx).get(k)
        if pD and a >= cap["as_on"]:
            net -= pD[1]
            bought -= pD[1]
    if reason is None and a == c["end_day"]:
        pv = _prev_capture(sp, c, ctx)
        if pv and (pv["start"] or pv["early"]) and k in _purchases_on(sp, pv["as_on"], ctx):
            reason = "purchase_on_start"
    return dict(figure=float(c["units"]) + net, closing=c, sold=sold, returned=ret, bought=bought, upto=a, key=k,
                approx=bool(c["approx"] or len(fam) > 1 or reason), approx_reason=reason, family=fam, taps=taps(con, sp, name, c["stamp_iso"], ctx))
'''))
SF.append(("F6 early_bill() retired (folded into start_marks / marg)", '''def early_bill(sp, k20, cap):
    """The early-morning capture (R3, R2-B3): a capture printed day D and taken before 09:00 on D stands for the end of D-1, but it can
    hold a bill dated D keyed before it. True when the key has a PURCHASE dated D in such a capture -- 'not judged on this closing'."""
    if cap is None:
        return False
    si = str(cap.get("stamp_iso") or "")
    if si[:10] != str(cap.get("as_on") or "") or si[11:16] >= "09:00":
        return False
    r = sp.q("SELECT 1 AS x FROM sp_move WHERE k20=? AND kind='PURCHASE' AND date=? LIMIT 1", k20, cap["as_on"])
    return bool(r)


''', '''# S587: the early-morning rule (a capture printed D taken before 09:00 holding a bill dated D) is start_marks / marg() -- one rule for the
# early and the start capture; its one caller, the voucher guard, reads marg()['approx_reason'].


'''))
SF.append(("F7 shelf(): no boundary on a key whose morning capture holds its purchase", '''    if n == 1 and mine["kind"] == "count" and cap is not None:   # S454 9.1: a bill dated before the count, entered after it
''', '''    if n == 1 and mine["kind"] == "count" and cap is not None and not (   # S454 9.1: a bill dated before the count, entered after it
            (cap.get("start") or cap.get("early")) and k in _purchases_on(sp, cap["as_on"], ctx)):   # S587 (R2-B3): never on a morning capture holding this key's purchase
'''))
SF.append(("F8 main(): verify-start", '''def main(argv):
    if not argv or argv[0] != "witness":
        print("usage: stock_figure.py witness   (the nightly side-by-side file; read only)")
        return 2
    for flag in ("/root/finance/_off/ALL_OFF", os.path.join(HERE, "_off", "ALL_OFF")):
        if os.path.exists(flag):
            print("stock_figure: switched off (%s)" % flag)
            return 0
    db = os.environ.get("FINANCE_DB") or os.path.join(HERE, "finance.db")
    con = sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=60)
    sp = _sw().Spine()
    p = witness(con, sp)
    con.close()
    print("stock_figure witness written: %s" % p)
    return 0
''', '''def verify_start_cli(con, sp, days=21):
    """`python3 stock_figure.py verify-start`: judge every start capture of the last `days` days that has no final verdict (captures() with a
    writable connection writes the record), then print each with its verdict, reason, the deciding keys and the excluded keys by cause.
    The installer runs it once after placing; the walk and the report quote it."""
    ctx = Ctx(con, sp)
    lines = []
    for r in start_report(con, sp, ctx, days=days):
        lines.append("start capture %s printed %s taken %s -> stands for the end of %s: %s%s (usable %s; keys %s, excluded %s, unexplained %s; prev %s %s)"
                     % (r["md5"], r["as_on"], r["stamp_iso"], r["start_day"], r["verdict"], (" / " + r["reason"]) if r["reason"] else "", r["usable"],
                        r["n_keys"], r["n_excluded"], r["n_unexplained"], str((r["prev"] or {}).get("md5") or "")[:8], (r["prev"] or {}).get("stamp_iso") or "-"))
        if r["sale_before"]:
            lines.append("   a sale came before it: %s" % ", ".join("%s %+g (sold %g)" % (x[1], x[2], x[3]) for x in r["sale_before"][:12]))
        if r["unexplained"]:
            lines.append("   unexplained: %s" % ", ".join("%s %+g" % (x[1], x[2]) for x in r["unexplained"][:12]))
        if r["excluded"]:
            lines.append("   excluded by cause: %s" % ", ".join("%s %d" % (k, v) for k, v in sorted(r["excluded"].items())))
        if r["changed_excluded"]:
            lines.append("   excluded keys that changed: %s" % ", ".join("%s %+g" % (x[1], x[2]) for x in r["changed_excluded"][:12]))
    return lines


def main(argv):
    if not argv or argv[0] not in ("witness", "verify-start"):
        print("usage: stock_figure.py witness   (the nightly side-by-side file; read only)")
        print("       stock_figure.py verify-start   (S587: judge the start-of-day closings of the last 21 days; writes stock_start_capture)")
        return 2
    for flag in ("/root/finance/_off/ALL_OFF", os.path.join(HERE, "_off", "ALL_OFF")):
        if os.path.exists(flag):
            print("stock_figure: switched off (%s)" % flag)
            return 0
    db = os.environ.get("FINANCE_DB") or os.path.join(HERE, "finance.db")
    if argv[0] == "verify-start":
        con = sqlite3.connect(db, timeout=60)
        sp = _sw().Spine()
        try:
            for line in verify_start_cli(con, sp):
                print(line)
        finally:
            con.close()
        return 0
    con = sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=60)
    sp = _sw().Spine()
    p = witness(con, sp)
    con.close()
    print("stock_figure witness written: %s" % p)
    return 0
'''))

# =============================================================================================================== shelf_figure.py (3.2: ONE edit)
SH = []
SH.append(("H1 record_gaps: tryable reads the one cover (con, ctx)", '''    covered = sorted({c["end_day"] for c in SF.usable_captures(sp, ctx) if SF.tryable(c, R)[0]})
''', '''    covered = sorted({c["end_day"] for c in SF.usable_captures(sp, ctx) if SF.tryable(c, R, con, ctx)[0]})   # S587 (R2-B4): purchase_cover -- one cover with the proof
'''))

# =============================================================================================================== stock_app.py (3.3)
SA = []
SA.append(("A1 the voucher guard reads marg()'s approx reason (early_bill retired)", '''    if _sf.early_bill(sp, M["key"], c) or _sf.late_purchase(con, sp, item, c, after, sh, tol, ctx):
''', '''    if M.get("approx_reason") == "purchase_on_start" or _sf.late_purchase(con, sp, item, c, after, sh, tol, ctx):   # S587 (R2-B3): the one morning rule is marg()'s
'''))
SA.append(("A2 _s488_why: tryable with con / ctx (the cover)", '''            c = after[0]
            _ok, short = _s524_tryable(c, _s524_reach(sp))
            why = "pur_behind" if short == "pur" else "no_figure"
''', '''            c = after[0]
            _ok, short = _s524_tryable(c, _s524_reach(sp), con, _sf.Ctx(con, sp))   # S587: the purchase half is purchase_cover
            why = "pur_behind" if short == "pur" else "no_figure"
'''))
SA.append(("A3 _s488_why: the bare-dict call too", '''                    _ok, short = _s524_tryable(dict(end_day=_s570_push_end(push[0], push[1]), stamp=_s570_stamp(push[1])), _s524_reach(sp))
''', '''                    _ok, short = _s524_tryable(dict(end_day=_s570_push_end(push[0], push[1]), stamp=_s570_stamp(push[1])), _s524_reach(sp), con, _sf.Ctx(con, sp))   # S587
'''))
SA.append(("A4 the stage's words: the pending_fix line (F-933)", '''        owner_lines = [dict(cls="warn", target="stock", text=r["text"]) for r in wrong]
        # S537 (2.3, R1-9a): the guard's lines -- the owner's only; Amir never sees a held line. One line per held item, then one summary
''', '''        owner_lines = [dict(cls="warn", target="stock", text=r["text"]) for r in wrong]
        for pf in _s587_pending_fix(st):                       # S587 (F-933): his tap, not a Marg fact -- an info line, never 'wrong' (D737 §3 F)
            owner_lines.append(dict(cls="info", target="stock", text="%s: Amir marked it done %s \\u2014 judged on the next closing taken after it"
                                    % (pf.get("item"), _s587_dm_hm(pf.get("done_at")))))
        # S537 (2.3, R1-9a): the guard's lines -- the owner's only; Amir never sees a held line. One line per held item, then one summary
'''))
SA.append(("A5 _s587_pending_fix / _s587_dm_hm before _s521_stage_words", '''def _s521_stage_words(con, st):
    """{state, lines: [{hi, anchor}], card_hi, board_hi, owner_en, owner_lines: [dict(cls, target, text)], wrong_rows, questions} for the''',
           '''def _s587_pending_fix(st):
    """S587 (F-933): the proof rows a correction of Amir's (an amir_job 'fix:' row done AFTER the judged capture) holds back from 'wrong' --
    stage A's proof, or every unverified lot of stage C (amir_stage puts them in C['pending_fix']). [dict(item, done_at, closing_day)]."""
    st = st or {}
    if st.get("stage") == "A":
        return list(((st.get("A") or {}).get("proof") or {}).get("pending_fix") or [])
    if st.get("stage") == "C":
        return list((st.get("C") or {}).get("pending_fix") or [])
    return []


def _s587_dm_hm(ts):
    s = str(ts or "").replace("T", " ")
    return ("%s-%s %s" % (s[8:10], s[5:7], s[11:16])) if len(s) >= 16 else s


def _s521_stage_words(con, st):
    """{state, lines: [{hi, anchor}], card_hi, board_hi, owner_en, owner_lines: [dict(cls, target, text)], wrong_rows, questions} for the'''))
SA.append(("A6 _s524_closings retired", '''def _s524_closings(sp):
    """[{as_on, stamp, stamp_iso, end_day}] -- every closing the spine holds (one per printed day, admitted by the spine's own rule), with its
    export's capture; a clean one carries end_day, a mid-day capture None. No second 'whole' bar is computed here (R1-B7)."""
    out = []
    for r in sp.q("SELECT c.as_on AS as_on, e.stamp AS stamp FROM (SELECT DISTINCT as_on, source_md5 FROM sp_close) c "
                  "JOIN sp_export e ON e.md5 = c.source_md5 ORDER BY c.as_on, e.stamp"):
        si = _s524_stamp_iso(r["stamp"])
        out.append(dict(as_on=str(r["as_on"]), stamp=str(r["stamp"] or ""), stamp_iso=si, end_day=(_s524_end_day(str(r["as_on"]), si) if si else None)))
    return out


''', '''# S587: _s524_closings is retired -- the proof reads stock_figure.captures() (every capture by md5, a start capture once accepted: D740),
# never sp_close by printed day.


'''))
SA.append(("A7 _s524_tryable passes con / ctx", '''def _s524_tryable(c, reach):
    """S577: stock_figure.tryable -- (ok, short), moved verbatim; record_gaps reads the same rule (charter 1b)."""
    return _sf.tryable(c, reach)
''', '''def _s524_tryable(c, reach, con=None, ctx=None):
    """S577: stock_figure.tryable -- (ok, short); record_gaps reads the same rule (charter 1b). S587: the purchase half is purchase_cover
    (the reach, the newest exports after the closing, or Amir's visit cover -- the last needs con / ctx)."""
    return _sf.tryable(c, reach, con, ctx)
'''))
SA.append(("A8 _s524_table: the captures, every usable try (R2-B5), N inside both reaches", '''    closings = _s524_closings(sp)
    clean = [c for c in closings if c["end_day"]]
    before = [c for c in clean if c["stamp_iso"] < first_at]
    R = max(before, key=lambda c: (c["as_on"], c["stamp_iso"])) if before else None
    after = sorted([c for c in clean if c["stamp_iso"] > last_at], key=lambda c: (c["stamp_iso"], c["as_on"]))
    T = dict(R=R, after=after, tries=[], keys={}, kof={}, reach=None, mixed=set(), closings=closings, N=None, N_short="")
    if R is None or not after:
        return T
    reach = _s524_reach(sp)
    T["reach"] = reach
    N = after[-1]                                              # S528 (F-851, charter 1b): the NEWEST capture -- "wrong" only when it, inside the reach, disagrees
    _N_ok, N_short = _s524_tryable(N, reach)
    T["N"], T["N_short"] = N, N_short
    # the tries: the FIRST clean closing after the vouchers and the NEWEST one the spine's reach covers (S520's first-or-newest, read with
    # R1-B2: a purchase export captured before the newest closing would otherwise pin the judgment to the first closing for days)
    tryable = [c for c in after if _s524_tryable(c, reach)[0]]
    tries = []
    if tryable and tryable[0] is after[0]:
        tries.append(after[0])
        if tryable[-1] is not after[0]:
            tries.append(tryable[-1])
    T["tries"] = tries
    if not tries:
        return T
    mixed = _s524_mixed(sp)
    T["mixed"] = mixed
    kof = {}
    kctx = _sf.Ctx(con, sp)                                    # S577: one identity context for the table
''', '''    kctx = _sf.Ctx(con, sp)                                    # S577 / S587: ONE context for the table -- identity, the captures, the cover
    closings = _sf.captures(sp, kctx)                          # S587: every capture by md5 (a start capture once accepted, D740); never sp_close by printed day
    clean = [c for c in closings if c["usable"]]
    before = [c for c in clean if c["stamp_iso"] < first_at]
    R = max(before, key=lambda c: (c["as_on"], c["stamp_iso"])) if before else None
    after = sorted([c for c in clean if c["stamp_iso"] > last_at], key=lambda c: (c["stamp_iso"], c["as_on"]))
    T = dict(R=R, after=after, tries=[], keys={}, kof={}, reach=None, mixed=set(), closings=closings, N=None, N_short="", N_ok=False)
    if R is None or not after:
        return T
    reach = _s524_reach(sp)
    T["reach"] = reach
    N = after[-1]                                              # S528 (F-851, charter 1b): the NEWEST capture -- "wrong" only when it, inside BOTH reaches, disagrees
    N_ok, N_short = _s524_tryable(N, reach, con, kctx)
    T["N"], T["N_short"], T["N_ok"] = N, N_short, N_ok
    # S587 (R2-B5): EVERY usable capture after the vouchers that the SALE reach covers is tried for ok=True, whatever its purchase cover -- an
    # agreeing voucher is proven at once; ok=False is read from N alone, and only while N is inside both reaches (purchase_cover, §3.2)
    tries = []
    for c in after:
        ok_c, short_c = _s524_tryable(c, reach, con, kctx)
        if ok_c or short_c == "pur":
            tries.append(c)
    T["tries"] = tries
    if not tries:
        return T
    mixed = _s524_mixed(sp)
    T["mixed"] = mixed
    kof = {}
'''))
SA.append(("A9 _s524_table: close_of by the capture's md5; the morning keys", '''    def close_of(c):
        return {str(r["k20"]): float(r["units"] or 0) for r in sp.q("SELECT k20, units FROM sp_close WHERE as_on=?", c["as_on"])}
    cR = close_of(R)
''', '''    def close_of(c):                                           # S587: the capture's OWN rows by key (sp_close_name over its md5; the '' key dropped)
        return {k: float(sum(u for (_n, _p, u) in rows)) for k, rows in _sf._cn_rows(sp, c["md5"], kctx)[1].items() if k}
    cR = close_of(R)
    pR = _sf.morning_skip_keys(sp, R, kctx)                    # S587 (R2-B3): keys a morning capture (start / early) cannot judge -- on R, and per try below
'''))
SA.append(("A10 _s524_table: the morning keys of a try are skipped", '''        cX = close_of(X)
        mv = {}
''', '''        cX = close_of(X)
        pX = _sf.morning_skip_keys(sp, X, kctx)
        mv = {}
'''))
SA.append(("A11 _s524_table: why = purchase_on_start / start_excluded", '''            if k in mixed:
                t["why"] = "mixed"
            elif k not in cX:
                t["why"] = "absent_at_try"
''', '''            if k in mixed:
                t["why"] = "mixed"
            elif k in pR or k in pX:                           # S587 (R2-B3): a purchase of the printed day inside R or X (or a sale the verification could not place)
                t["why"] = pR.get(k) or pX.get(k)
            elif k not in cX:
                t["why"] = "absent_at_try"
'''))
SA.append(("A12 _s524_table: the verdicts -- N inside both reaches; pending_fix (F-933)", '''    for k, e in keys.items():
        given = [t for t in e["tries"] if t["ok"] is not None]
        prov = [t for t in given if t["ok"]]
        tN = next((t for t in e["tries"] if t["X"] is N), None)   # the try dicts hold the `after` objects: identity is sound
        e["proven"] = bool(prov)
        e["wrong"] = (not prov) and (tN is not None) and (tN["ok"] is False)              # S528 (F-851): wrong only by the newest capture
        e["pending_reach"] = (not prov) and bool(given) and (tN is None)                   # a False stands, N not judgeable yet (R1-C2)
        e["L"] = prov[0] if prov else (tN if tN else (given[-1] if given else (e["tries"][-1] if e["tries"] else None)))
    T["keys"] = keys
    return T
''', '''    fixes = _s587_fix_done(con)                                # S587 (F-933): {item: done_at} -- Amir's 'fix:' jobs called done
    for k, e in keys.items():
        given = [t for t in e["tries"] if t["ok"] is not None]
        prov = [t for t in given if t["ok"]]
        tN = next((t for t in e["tries"] if t["X"] is N), None) if N_ok else None   # S587: N judges only inside both reaches; the try dicts hold the `after` objects
        e["proven"] = bool(prov)
        e["wrong"] = (not prov) and (tN is not None) and (tN["ok"] is False)              # S528 (F-851): wrong only by the newest capture
        e["pending_reach"] = (not prov) and bool(given) and (tN is None)                   # a False stands, N not judgeable yet (R1-C2)
        e["pending_fix"] = None
        if e["wrong"]:                                         # S587 (F-933): a correction he marked done AFTER the judged capture -- judged on the next capture
            nts = str(N.get("stamp_iso") or "").replace("T", " ")[:19]
            late_fix = [(it, fixes[it]) for it in sorted(e["items"]) if it in fixes and fixes[it] > nts]
            if late_fix:
                e["wrong"], e["pending_fix"] = False, dict(item=late_fix[0][0], done_at=late_fix[0][1])
        e["L"] = prov[0] if prov else (tN if tN else (given[-1] if given else (e["tries"][-1] if e["tries"] else None)))
    T["keys"] = keys
    return T


def _s587_fix_done(con):
    """S587 (F-933): {item: done_at ('YYYY-MM-DD HH:MM:SS')} of every amir_job 'fix:' row called done (his tap, or seen in Marg) -- the
    newest per item."""
    out = {}
    try:
        for subj, at in con.execute("SELECT subject, MAX(replace(done_at,'T',' ')) FROM amir_job WHERE key LIKE 'fix:%' AND done_at IS NOT NULL GROUP BY subject"):
            out[str(subj)] = str(at or "")[:19]
    except Exception:                                          # noqa: BLE001
        pass
    return out
'''))
SA.append(("A13 _s524_verdict: pending_fix rows", '''    base = dict(rows=[], unseen=[], last_at=last_at, items=0, proven_on={}, text="")
''', '''    base = dict(rows=[], unseen=[], last_at=last_at, items=0, proven_on={}, text="", pending_fix=[])   # S587 (F-933): pending_fix beside the rows
'''))
SA.append(("A14 _s524_verdict: the collectors", '''    rows, unseen, proven_on = [], [], {}

    def wd(fn, v, item, pk):''', '''    rows, unseen, proven_on, pending_fix = [], [], {}, []

    def wd(fn, v, item, pk):'''))
SA.append(("A15 _s524_verdict: an unseen row by pending_fix", '''        else:
            if e and e.get("pending_reach"):                     # S528 (F-851): judgeable only once the spine reaches the newest closing
                unseen.append(dict(row, why="reach_" + (T.get("N_short") or "sale")))
            else:
                unseen.append(dict(row, why=((t or {}).get("why") or "no_verdict")))
    state = "done" if (not rows and not unseen) else ("wrong" if rows else "export")
    res = dict(base, state=state, rows=rows, unseen=unseen, items=len(items), proven_on=proven_on, as_before=_s524_dmy(R["as_on"]),
               as_after=_s524_dmy(L["as_on"]))
''', '''        else:
            if e and e.get("pending_fix"):                       # S587 (F-933): his correction came after the judged capture -- judged on the next one
                unseen.append(dict(row, why="pending_fix", fix_done_at=e["pending_fix"]["done_at"]))
                pending_fix.append(dict(item=item, key=k, done_at=e["pending_fix"]["done_at"], closing_day=_s524_dmy(X["as_on"])))
            elif e and e.get("pending_reach"):                   # S528 (F-851): judgeable only once the spine reaches the newest closing
                unseen.append(dict(row, why="reach_" + (T.get("N_short") or "sale")))
            else:
                unseen.append(dict(row, why=((t or {}).get("why") or "no_verdict")))
    state = "done" if (not rows and not unseen) else ("wrong" if rows else "export")
    res = dict(base, state=state, rows=rows, unseen=unseen, items=len(items), proven_on=proven_on, as_before=_s524_dmy(R["as_on"]),
               as_after=_s524_dmy(L["as_on"]), pending_fix=pending_fix)
'''))
SA.append(("A17 _s524_verdict: a proof waiting ONLY on his corrections says so (why pending_fix)", '''    if state == "export":
        pend = any(((T["keys"].get(kof.get(it) or it) or {}).get("pending_reach")) for it in items)
        res.update(_s488_why(con, sp, T["closings"], R, ([T["N"]] if (pend and T.get("N")) else after), last_at))   # S528: the newest capture is what it waits for
    return res
''', '''    if state == "export":
        pend = any(((T["keys"].get(kof.get(it) or it) or {}).get("pending_reach")) for it in items)
        res.update(_s488_why(con, sp, T["closings"], R, ([T["N"]] if (pend and T.get("N")) else after), last_at))   # S528: the newest capture is what it waits for
        if pending_fix and all(u.get("why") == "pending_fix" for u in unseen) and T.get("N"):   # S587 (F-933): the wait is his correction, not a report
            res.update(why="pending_fix", closing_day=_s524_dmy(T["N"]["as_on"]), closing_at=T["N"].get("stamp_iso"))
    return res
'''))
SA.append(("A18 the stage's English for a proof waiting on his corrections (stage A)", '''                en = (("Stage A: all %d entered \\u2014 %s" % (tot, landed_en())) if landed else                        # S584
                      "Stage A: all %d entered \\u2014 waiting: %s" % (tot, _s524_english_ending(pr) or "for the closing-stock export that proves them"))
''', '''                en = (("Stage A: all %d entered \\u2014 %s" % (tot, landed_en())) if landed else                        # S584
                      ("Stage A: all %d entered \\u2014 %s" % (tot, fix_en(pr))) if pr.get("why") == "pending_fix" else   # S587 (F-933)
                      "Stage A: all %d entered \\u2014 waiting: %s" % (tot, _s524_english_ending(pr) or "for the closing-stock export that proves them"))
'''))
SA.append(("A19 the stage's English for a proof waiting on his corrections (stage C)", '''                en = (("Stage C: lot %d entered on %s \\u2014 %s" % (lot, _s524_dmy(str(pr.get("last_at") or "")[:10]) or "?", landed_en())) if landed else   # S584
                      "Stage C: lot %d entered on %s \\u2014 waiting: %s" % (lot, _s524_dmy(str(pr.get("last_at") or "")[:10]) or "?",
                                                                          _s524_english_ending(pr) or "for the closing-stock export"))
''', '''                en = (("Stage C: lot %d entered on %s \\u2014 %s" % (lot, _s524_dmy(str(pr.get("last_at") or "")[:10]) or "?", landed_en())) if landed else   # S584
                      ("Stage C: lot %d entered on %s \\u2014 %s" % (lot, _s524_dmy(str(pr.get("last_at") or "")[:10]) or "?", fix_en(pr))) if pr.get("why") == "pending_fix" else   # S587 (F-933)
                      "Stage C: lot %d entered on %s \\u2014 waiting: %s" % (lot, _s524_dmy(str(pr.get("last_at") or "")[:10]) or "?",
                                                                          _s524_english_ending(pr) or "for the closing-stock export"))
'''))
SA.append(("A20 fix_en() beside landed_en()", '''        def landed_en():
            return "purchase report landed %s \\u2014 judged at the spine's next build (within 10 minutes)" % landed[11:16]
''', '''        def landed_en():
            return "purchase report landed %s \\u2014 judged at the spine's next build (within 10 minutes)" % landed[11:16]

        def fix_en(p):                                         # S587 (F-933): the lot waits on HIS corrections, made after the judged closing
            n = len((p or {}).get("pending_fix") or [])
            return "%d item%s Amir marked done after Marg's closing of %s \\u2014 judged on the next closing taken after it" % (n, "" if n == 1 else "s", (p or {}).get("closing_day") or "?")
'''))
SA.append(("A16 amir_stage: C carries the lots' pending_fix rows", '''             wrong=[r for l in lots if not l["verified"] for r in l["proof"].get("rows", [])],
''', '''             wrong=[r for l in lots if not l["verified"] for r in l["proof"].get("rows", [])],
             pending_fix=[pf for l in lots if not l["verified"] for pf in (l["proof"].get("pending_fix") or [])],   # S587 (F-933)
'''))

# =============================================================================================================== stock_watch.py (3.4)
SW = []
SW.append(("W1 version", '''VERSION = "1.7"
KIT = "S584_SMALL_FIXES"                                      # v1.6 was S583_ARRIVALS_ONE_RULE, v1.5 S577_STOCK_ON_SPINE, v1.4 S502_STOCK_MILAAN_TODAY
''', '''VERSION = "1.8"
KIT = "S587_MORNING_FLOW"                                     # v1.7 was S584_SMALL_FIXES, v1.6 S583_ARRIVALS_ONE_RULE, v1.5 S577_STOCK_ON_SPINE
# v1.8 (S587, 18-Oct-2026, D740): two settings under "Counts & watch" -- count.start_capture (the start-of-day closing on / off) and
# count.start_unexplained_max (items that may change with no Marg reason before such a closing is set aside); stock_figure reads them through
# settings(); needs_you_lines gains start_capture_lines (the set-aside / waiting start captures of the last 7 days, English).
'''))
SW.append(("W2 the two rows after count.bad_pct", '''    dict(key="count.bad_pct", label="Full count: bad leakage (%)", kind="pct", default="2.0", seed="2.0", lo=0, hi=100,
         hint="A closed full count at or over this share of sales moves the cadence to monthly."),
''', '''    dict(key="count.bad_pct", label="Full count: bad leakage (%)", kind="pct", default="2.0", seed="2.0", lo=0, hi=100,
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
'''))
SW.append(("W3 settings(): the two friendly keys", '''                bill_grace_days=max(1, num("arrival.bill_grace_days", 3, int)), back_days=max(0, num("arrival.back_days", 2, int)),
                budget_pct=num("leak.budget_pct", 1.0), red_periods=max(1, num("leak.red_periods", 2, int)))
''', '''                bill_grace_days=max(1, num("arrival.bill_grace_days", 3, int)), back_days=max(0, num("arrival.back_days", 2, int)),
                budget_pct=num("leak.budget_pct", 1.0), red_periods=max(1, num("leak.red_periods", 2, int)),
                start_capture=str(out["count.start_capture"]).strip() not in ("0", "off", "no"),            # S587 (D740): stock_figure reads these two
                start_unexplained_max=max(0, num("count.start_unexplained_max", 3, int)))
'''))
SW.append(("W4 needs_you_lines: the start-capture lines", '''        out.extend(leak_needs_you(con, S, sp))
        out.extend(arrival_needs_you(con, sp))                  # S583
        return out
''', '''        out.extend(leak_needs_you(con, S, sp))
        out.extend(arrival_needs_you(con, sp))                  # S583
        out.extend(start_capture_lines(con, sp))                # S587 (D740)
        return out
'''))
SW.append(("W5 start_capture_lines after arrival_needs_you", '''# ------------------------------------------------------------------ 3.3 the roster
def _spot_day(S, d=None):''', '''def start_capture_lines(con, sp=None):
    """S587 (D740, §3.1): the owner's English lines for the start-of-day closings (stock_figure's record stock_start_capture): one per capture
    SET ASIDE in the last 7 days, naming the items that decided it by their printed names; one for a capture still PENDING more than a day after
    its day's sale report landed ('waits for Amir's purchase export'). Nobody is asked to re-print; Darpan and Shavez see nothing. Fail-soft."""
    out = []
    try:
        if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='stock_start_capture'").fetchone():
            return out
        sp = sp or Spine()
        SF = _sf()
        lo = (today() - dt.timedelta(days=7)).isoformat()
        R = SF.reach(sp) if sp.ok else {}
        for as_on, si, verdict, reason, detail in con.execute("SELECT as_on, stamp_iso, verdict, reason, detail FROM stock_start_capture WHERE as_on>=? ORDER BY stamp_iso", (lo,)):
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
                landed = SF.sale_landed(sp, as_on)
                if landed and (today() - dt.date.fromisoformat(landed)).days > 1:
                    out.append(dict(cls="info", target="stock", text="Closing stock of %s waits for Amir's purchase export" % when))
    except Exception:                                         # noqa: BLE001
        return out
    return out


# ------------------------------------------------------------------ 3.3 the roster
def _spot_day(S, d=None):'''))

# =============================================================================================================== amir_day.py (3.5)
AD = []
AD.append(("Y1 KIT", '''KIT = "S584_SMALL_FIXES"                                   # F-881: the kit that last placed this file (S533 built the page; S537, S577, S583 read it)
''', '''KIT = "S587_MORNING_FLOW"                                  # the kit that last placed this file (S533 built the page; S584 named it; S587: the export step last, the re-export line)
'''))
AD.append(("Y2 ORDER, pos, id_at after GATE_STEPS", '''# Steps that decide whether a day is finished.  Step 1 is a nudge, step 3 an instruction, step 7 the close itself.
GATE_STEPS = (2, 4, 5, 6)
''', '''# Steps that decide whether a day is finished.  Step 1 is a nudge, step 3 an instruction, step 7 the close itself.
GATE_STEPS = (2, 4, 5, 6)

# S587 (fix D of D737; the approved mock-up): the DISPLAY order of the steps -- Marg sudhar (id 6) before the Export (id 3), so the purchase
# report is taken after every entry of the morning.  Ids never change: every route, S.done, the gate, amir_step_log.step and the duty map's
# due_sql keep them (history is not rewritten).  pos(id) is the number the banner shows; id_at(pos) the step at that position.
ORDER = (1, 2, 6, 3, 4, 5, 7)
LABEL_OF = dict(STEPS)


def pos(step_id):
    return ORDER.index(int(step_id)) + 1


def id_at(position):
    return ORDER[max(1, min(7, int(position))) - 1]
'''))
AD.append(("Y3 _reexport_due before state()", '''def state(cx, day, who="", step=None, owner=False):
    """Every fact the pages need, read once.''', '''def _reexport_due(cx, day, ticks):
    """S587 (F-926 / D737 D): (due, since) -- True when the day's newest step-2 tap ('Sab bill daal diye') is later than the newest export fact of
    the day: his newest step-3 tap ('Dono report nikaal di'), or the newest VERIFIED purchase export that LANDED in mi_file that day (received_at;
    a fresh export landing after the tap clears it too -- the fact, not the tap, as S584's E).  False while nothing of either kind exists (then
    the step-4 gate says the report is not taken).  Rests on HIS taps (D712).  since = the step-2 tap's moment."""
    t2 = _norm_ts((ticks.get(2) or {}).get("done_at"))
    if not t2:
        return False, None
    marks = [_norm_ts((ticks.get(3) or {}).get("done_at"))]
    try:
        if _table_exists(cx, "mi_file"):
            r = cx.execute("SELECT MAX(substr(replace(received_at,'T',' '),1,19)) FROM mi_file WHERE verdict='VERIFIED' "
                           "AND type IN ('PURCHASE_BILLWISE','PURCHASE_ITEMWISE','PURCHASE_BILLITEMWISE') AND substr(replace(received_at,'T',' '),1,10)=?",
                           (day,)).fetchone()
            marks.append(_norm_ts(r[0]) if r and r[0] else None)
    except Exception:                                                  # noqa: BLE001
        pass
    marks = [m for m in marks if m]
    if not marks:
        return False, None
    return (t2 > max(marks)), t2


def state(cx, day, who="", step=None, owner=False):
    """Every fact the pages need, read once.'''))
AD.append(("Y4 state(): reexport_due read once", '''    S.export_none = any(e.get("state") == "none" for e in S.exports)
''', '''    S.export_none = any(e.get("state") == "none" for e in S.exports)
    S.reexport_due, S.reexport_since = _reexport_due(cx, day, S.ticks)   # S587 (F-926 / D737 D)
'''))
AD.append(("Y5 _derive: the re-export gate line", '''    if not S.done[2]:
        gate.append((2, "Bill daalne ki pushti baaki hai", "bills not confirmed entered"))
    for e in S.exports:
''', '''    if not S.done[2]:
        gate.append((2, "Bill daalne ki pushti baaki hai", "bills not confirmed entered"))
    if getattr(S, "reexport_due", False):                     # S587 (F-926 / D737 D): a bill entered after the export -- the day waits for a fresh export
        gate.append((3, "Purchase report dobara nikaalni hai — bill entry export ke baad hui hai", "re-export due: a bill was entered after the export"))
    for e in S.exports:
'''))
AD.append(("Y6 _next_step walks ORDER", '''def _next_step(S):
    for n, _label in STEPS:
        if n == 7:
''', '''def _next_step(S):
    for n in ORDER:                                            # S587: the display order (ids unchanged)
        if n == 7:
'''))
AD.append(("Y7 _ready_to_close: not while a re-export is due", '''def _ready_to_close(S):
    return all(S.done.get(n) for n in GATE_STEPS)
''', '''def _ready_to_close(S):
    return all(S.done.get(n) for n in GATE_STEPS) and not getattr(S, "reexport_due", False)   # S587: the day does not close until a fresh export
'''))
AD.append(("Y8 _banner: positions in ORDER", '''    out = ["<div class=steps>"]
    for n, label in STEPS:
        if n == current:
            cls = "on"
        elif S.done.get(n):
            cls = "ok"
        elif n == 4 and S.export_wait:
            cls = "wait"
        else:
            cls = ""
        out.append("<a class='%s' href='/finance/amir/step/%d'>%d<br>%s</a>" % (cls, n, n, _esc(label)))
''', '''    out = ["<div class=steps>"]
    for p, n in enumerate(ORDER, 1):                           # S587: the position shown, the id in the route
        label = LABEL_OF[n]
        if n == current:
            cls = "on"
        elif S.done.get(n):
            cls = "ok"
        elif n == 4 and S.export_wait:
            cls = "wait"
        else:
            cls = ""
        out.append("<a class='%s' href='/finance/amir/step/%d'>%d<br>%s</a>" % (cls, n, p, _esc(label)))
'''))
AD.append(("Y9 _page: Step N of 7 by position; the red re-export band on the later positions", '''    card = row_marg_sudhar(S, top=True) if step != 6 else ""
    return _shell("Amir -- kaam", who + _banner(step, S) + card + _notes_html(S) + head + body + _neft_card_s407()
                  + "<p class=foot>Step %d of 7 &middot; <a href='/portal?all=1'>Sab tiles</a></p>" % step, head_extra)
''', '''    card = row_marg_sudhar(S, top=True) if step != 6 else ""
    band = _reexport_band(S) if (getattr(S, "reexport_due", False) and pos(step) >= 4) else ""   # S587: on every step after the export's position
    return _shell("Amir -- kaam", who + _banner(step, S) + band + card + _notes_html(S) + head + body + _neft_card_s407()
                  + "<p class=foot>Step %d of 7 &middot; <a href='/portal?all=1'>Sab tiles</a></p>" % pos(step), head_extra)


def _reexport_band(S):
    """S587 (F-926 / D737 D): one red line on the positions after the export while a bill was entered after it -- the door is the export step."""
    return ("<div class=band id=reexport style='background:#fff4f4;border-color:var(--bad);color:var(--bad)'>"
            "Purchase report dobara nikaaliye &mdash; bill entry export ke baad hui hai. <a href='/finance/amir/step/3'>Kholiye</a></div>")
'''))
AD.append(("Y10 the POST redirect steps by position", '''        nxt = _next_step(S2)
        return _go(nxt if nxt >= n else n + 1 if n < 7 else 7)
''', '''        nxt = _next_step(S2)
        return _go(nxt if pos(nxt) >= pos(n) else id_at(pos(n) + 1) if pos(n) < 7 else 7)   # S587 (R1-B1): by position, never id arithmetic
'''))
AD.append(("Y11 the owner's day: re-export due since hh:mm", '''    cls, line = _salt_owner(S.salt)
    body += "<div class=card id=s444salt><h2>Salt list from Marg</h2><p class='big %s'>%s</p></div>" % (cls, _esc(line))
''', '''    if getattr(S, "reexport_due", False):                     # S587 (F-926): his line, same day -- Needs-you is not touched
        body += "<div class=card id=reexport><p class='big bad'>re-export due since %s</p><p class=sub>a bill was entered after the purchase export; the day waits for a fresh export</p></div>" % _esc(_hhmm(S.reexport_since))
    cls, line = _salt_owner(S.salt)
    body += "<div class=card id=s444salt><h2>Salt list from Marg</h2><p class='big %s'>%s</p></div>" % (cls, _esc(line))
'''))
AD.append(("Y12 the visit summary: skipped by position", '''    def tap_step(n, label, skipped_note):
        if n in ticks:
            return {"n": n, "label": label, "state": "done", "note": tick_note(n)}
        if closed or nxt > n:
            return {"n": n, "label": label, "state": "skipped", "note": skipped_note}
''', '''    def tap_step(n, label, skipped_note):
        if n in ticks:
            return {"n": n, "label": label, "state": "done", "note": tick_note(n)}
        if closed or pos(nxt) > pos(n):                        # S587 (R1-B1): by position
            return {"n": n, "label": label, "state": "skipped", "note": skipped_note}
'''))
AD.append(("Y13 the visit summary: the export step skipped by position", '''    elif closed or nxt > 3:
        steps.append({"n": 3, "label": "Export", "state": "skipped", "note": "no export tap"})
''', '''    elif closed or pos(nxt) > pos(3):                          # S587 (R1-B1): by position
        steps.append({"n": 3, "label": "Export", "state": "skipped", "note": "no export tap"})
'''))

# =============================================================================================================== stock_now.html (F-936)
NW = []
NW.append(("N1 the items table gets its own id", '''  <div style="overflow-x:auto;margin-top:8px"><table><thead><tr>
    <th>Item</th><th class="n">Ours</th><th class="n">Marg</th><th class="n">Gap</th>
''', '''  <div style="overflow-x:auto;margin-top:8px"><table id="itemtbl"><thead><tr>
    <th>Item</th><th class="n">Ours</th><th class="n">Marg</th><th class="n">Gap</th>
'''))
NW.append(("N2 the fifth heading joins the items table, never the readiness block's bills table", '''    document.querySelector("table thead tr").appendChild(th);
''', '''    document.querySelector("#itemtbl thead tr").appendChild(th);   /* S587 (F-936): the ITEMS table by id -- the first <thead> on the page is the readiness block's bills table */
'''))

EDITS = {"stock_figure.py": SF, "shelf_figure.py": SH, "stock_app.py": SA, "amir_day.py": AD, "stock_watch.py": SW, "stock_now.html": NW}


def apply(src, edits, label):
    raw = open(src, "rb").read()
    m = hashlib.md5(raw).hexdigest()
    if m != FROM[label]:
        print("STOP: %s is %s, not the FROM pin %s -- nothing built" % (src, m, FROM[label]))
        return None
    t = raw.decode("utf-8")
    for name, old, new in edits:
        n = t.count(old)
        if n != 1:
            print("STOP: %s anchor %s occurs %d times (must be exactly 1) -- nothing built" % (label, name, n))
            return None
        t = t.replace(old, new, 1)
        print("edit %s %s: anchored once, applied" % (label, name))
    return t.encode("utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    built = {}
    for label, edits in EDITS.items():
        out = apply(os.path.join(a.finance, label), edits, label)
        if out is None:
            return 2
        built[label] = out
    os.makedirs(a.out, exist_ok=True)
    for label, out in built.items():
        dst = os.path.join(a.out, label)
        with open(dst, "wb") as fh:
            fh.write(out)
        print("built %s md5 %s  (FROM %s)" % (dst, hashlib.md5(out).hexdigest(), FROM[label]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
