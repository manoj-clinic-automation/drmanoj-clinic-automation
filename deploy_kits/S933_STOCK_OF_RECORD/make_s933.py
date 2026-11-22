#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s933.py -- kit S933_STOCK_OF_RECORD (Session 504, 22-Nov-2026). Builds the TO files from the LIVE bytes by exact anchors:
    python3 make_s933.py <from dir: a copy of the live /root/finance> <to dir>
  stock_figure.py   S928's bill_units: the scan tie is the fact -- the arrived=1 gate dropped from _s928_order_match (F-series: a tap before
                    the scan left arrived=0 on 41 of 99 ties; the bill-over-tap rule was silent on them)
  stock_check.py    record(): every row from stock_record (the stock of record); the page computes nothing itself
  stock_check.html  the words: a bill keyed after the print, Marg behind a bill, clinic consumables, the closing's day
  item_ledger.py    the head figures (Marg stock / Expected) from the record
Every anchor must match exactly once, else it stops and writes nothing. Prints the md5 of each TO file."""
import hashlib
import io
import os
import re
import sys

FROM_MD5 = dict(stock_figure="8130315e01c7da5d24e1ba93f6e60ad8")   # S928's live file (22-Nov 16:59); the others are checked by anchor only


def rd(p):
    with io.open(p, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def wr(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with io.open(p, "w", encoding="utf-8", newline="") as fh:
        fh.write(s)


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def once(s, a, b, what):
    n = s.count(a)
    if n != 1:
        sys.exit("ANCHOR %s: found %d times, need exactly 1 -- nothing written" % (what, n))
    return s.replace(a, b)


def patch_figure(s):
    s = once(s, 'sids = sorted({int(r[0]) for r in con.execute("SELECT asset_bill_id FROM order_scan_tie WHERE order_id=? AND arrived=1 AND asset_bill_id IS NOT NULL", (int(order_id),))})',
             'sids = sorted({int(r[0]) for r in con.execute("SELECT asset_bill_id FROM order_scan_tie WHERE order_id=? AND asset_bill_id IS NOT NULL", (int(order_id),))})   # S933: the tie is the fact -- arrived=0 when reception tapped before the scan (41 of 99 live ties); the bill still speaks',
             "stock_figure _s928_order_match")
    s = once(s, 'KIT = "S928_STOCK_ONE_RULE"                              # v1.6 S928',
             'KIT = "S933_STOCK_OF_RECORD"                             # v1.7 S933 (the scan tie is the fact for bill_units), v1.6 S928', "stock_figure KIT")
    return s


NEW_RECORD = r'''def record(con):
    """Every figure of the page from THE STOCK OF RECORD (stock_record, kit S933): the page computes no stock figure itself. {ok, rows, counts,
    next_list, reports, totals, record, ...}."""
    SW, SF = _SW(), _SF()
    import stock_record as SR                                 # noqa: PLC0415 -- beside this file: the one stock record
    SW.ensure(con)
    sp = SW.Spine()
    if not SF.ready(sp):
        return dict(ok=False, reason="The stock record (the spine's closing table) is not ready: no figure of record yet.", rows=[], counts=[], at=now_ist())
    R_rows, M = SR.rows(con, sp, "never")                   # a page read never rebuilds the record inside the request (the finance app's connection)
    if not M.get("built_at"):
        R_rows, M = SR.rows(con, sp, "auto")                 # the very first read ever: built once, here
        if not M.get("built_at"):
            return dict(ok=False, reason="The stock of record has not been built yet (stock_record --build).", rows=[], counts=[], at=now_ist())
    rebuilding = False
    try:
        if SR.is_stale(con, sp):
            rebuilding = _rebuild_detached()                  # the cron's own command, now; the page shows the record it has and its build time
    except Exception:                                         # noqa: BLE001
        rebuilding = False
    ctx = SF.Ctx(con, sp)
    S = SW.settings(con)
    rows, covered = [], set()
    for d in R_rows:
        n = d["item"]
        pack = int(d.get("pack") or 1)
        forms = list(d.get("forms") or [])
        covered.add(norm(n))
        covered.update(norm(f) for f in forms)
        marg = int(round(float(d.get("marg_units") or 0)))
        core = d.get("shelf_units")
        core = int(round(core)) if core is not None else None
        gap = d.get("gap_units")
        gap = int(round(gap)) if gap is not None else None
        W = d.get("waiting") or []
        wait_u = float(d.get("waiting_units") or 0)
        lines = [dict(line_id=w.get("line_id"), vendor=w.get("vendor") or "", kind=w.get("kind") or "tap", at=str(w.get("at") or ""), units=w.get("units"), tap=w.get("tap"),
                      bill=w.get("bill"), stamp=w.get("stamp") or "", word=w.get("word") or "", short=float(w.get("short") or 0), pack=int(w.get("pack") or pack), state=w.get("state") or "")
                 for w in W]
        rows.append(dict(item=n, key=d.get("k20"), pack=pack, pieces=bool(d.get("pieces")), ortho=bool(d.get("ortho")), consumable=bool(d.get("consumable")),
                         marg=marg, marg_t=st(marg, pack), shelf=d.get("shelf_raw"), core=core, core_t=st(core, pack), arrived=wait_u,
                         arrived_t=(st(wait_u, pack, signed=True) if wait_u else ""), gap=gap, gap_t=(st(gap, pack, signed=True) if gap is not None else "—"),
                         named=d.get("shelf_named") or None, approx=bool(d.get("approx")), base_kind=d.get("base_kind") or None, base_day=d.get("base_day") or None,
                         base_at=d.get("base_at") or None, evening=bool(d.get("base_evening")), forms=forms, lines=lines, state=d.get("state") or "",
                         words=d.get("words") or "", late=d.get("late") or [], flags=d.get("marg_flag") or ""))
    # the count's names Marg no longer prints (not linked to any Marg name by the rename memory): the identity question is the way through
    count_only = []
    try:
        cf = SF.count_family(con, ctx)
        for c in sorted(cf):
            if norm(c) in covered:
                continue
            pk = SF.pack_of(con, sp, c, ctx)[0]
            if pk <= 1 and _has(con, "stock_count_item"):   # a name the spine never printed: the count's own pack size
                r = con.execute("SELECT pack_size FROM stock_count_item WHERE item=? ORDER BY count_id DESC LIMIT 1", (c,)).fetchone()
                pk = int((r[0] if r else 1) or 1)
            count_only.append(dict(item=c, counted_t=st(cf[c]["qty"], pk), day=dmy(cf[c]["day"])))
    except Exception:                                         # noqa: BLE001
        count_only = []
    # Darpan's counts: every spot / darpan point, newest first (30 days); older ones counted
    counts, older = [], 0
    try:
        lo = (today() - dt.timedelta(days=30)).isoformat()
        asked = {}
        if _has(con, "stock_spot_roster"):
            for pid, reason in con.execute("SELECT point_id, reason FROM stock_spot_roster WHERE point_id IS NOT NULL"):
                asked[int(pid)] = reason or ""
        for pid, item, at, q, e, g, basis, by, note, status in con.execute(
                "SELECT id, item, at, qty_units, expected_units, gap_units, basis, by, note, status FROM stock_point WHERE source IN ('spot','darpan') "
                "AND COALESCE(status,'')<>'superseded' ORDER BY at DESC, id DESC"):
            if str(at)[:10] < lo:
                older += 1
                continue
            pack = SF.pack_of(con, sp, item, ctx)[0]
            reason = asked.get(int(pid), "")
            counts.append(dict(id=pid, item=item, key=SF.key_of(sp, item, ctx), at=str(at)[:16], day=day_word(at), time=str(at)[11:16], qty_t=st(q, pack),
                               expected_t=(st(e, pack) if e is not None else "—"), gap_t=(st(g, pack, signed=True) if g is not None else "—"), gap=g, basis=basis or "",
                               by=(by or "").title(), asked=("you asked" in reason.lower()), reason=reason, note=_note_word(note), provisional=(status == "provisional"),
                               evening=SF.evening_count(at, S.get("evening_hour", 17), str(at)[:10]) if hasattr(SF, "evening_count") else False))
    except sqlite3.Error:
        pass
    # the next list: his asks first, then the system's picks
    nxt, asks = [], []
    try:
        nd = SW.next_roster_day(S)
        if nd is not None:
            nxt = [dict(item=x["item"], reason=x.get("reason") or "") for x in SW.preview_roster(con, nd, S, sp)][:12]
        asks = [dict(item=r[0], at=stamp(r[1]), by=(r[2] or "").title()) for r in con.execute("SELECT item, at, by FROM stock_watch_ask WHERE done_at IS NULL ORDER BY id")]
        nd_t = day_word(nd.isoformat()) if nd is not None else ""
    except Exception:                                         # noqa: BLE001
        nd_t = ""
    # the reports behind the page: the record's own closing
    kind_word = {"yesterday": "printed the next day, so it stands for the end of %s" % dmy(M.get("cap_end_day")),
                 "morning": "a morning print on its own day: it stands for the end of %s, the day before" % dmy(M.get("cap_end_day")),
                 "night": "a night print: it stands for the end of its own day"}.get(M.get("cap_kind"), "")
    reports = dict(closing_as_on=dmy(M.get("cap_end_day")), closing_printed=dmy(M.get("cap_as_on")), closing_at=stamp(M.get("cap_stamp_iso")), start=(M.get("cap_kind") == "morning"),
                   kind_word=kind_word, sale_to=dmy(M.get("sale_to")), purchase_to=dmy(M.get("purchase_to")), built_at=stamp(M.get("built_at")))
    rows.sort(key=lambda r: (r["gap"] is None, -abs(r["gap"] or 0), r["item"]))
    look = [r for r in rows if r["state"] in ("look", "waiting") and r["gap"] not in (None, 0)]
    tot = dict(items=len(rows), look=len(look), arrived=sum(1 for r in rows if r["arrived"]), noshelf=sum(1 for r in rows if r["state"] == "no_shelf"),
               agree=sum(1 for r in rows if r["gap"] == 0 and r["state"] in ("agree", "waiting")), agree_in_stock=sum(1 for r in rows if r["gap"] == 0 and r["state"] in ("agree", "waiting") and r["marg"] > 0),
               behind=sum(1 for r in rows if r["state"] == "marg_behind"), consumable=sum(1 for r in rows if r["state"] == "consumable"),
               late=sum(1 for r in rows if r["late"]), counts=len(counts), count_only=len(count_only))
    return dict(ok=True, at=now_ist(), rows=rows, counts=counts, older_counts=older, next_list=nxt, next_day=nd_t, asks=asks, count_only=count_only,
                reports=reports, totals=tot, evening_hour=S.get("evening_hour", 17), bill_over_tap=S.get("bill_over_tap", True), version=VERSION,
                record=dict(built_at=M.get("built_at"), n_rows=M.get("n_rows"), took_s=M.get("took_s"), version=M.get("version"), rebuilding=rebuilding))


def _rebuild_detached():
    """The record is stale: start `stock_record.py --build` as its own process (flock keeps one at a time, as the cron line does) and return at once.
    True when started. Never raises."""
    try:
        import subprocess                                     # noqa: PLC0415
        import shutil                                         # noqa: PLC0415
        env = dict(os.environ)
        env.setdefault("FINANCE_DB", os.environ.get("FINANCE_DB") or os.path.join(HERE, "finance.db"))
        env.setdefault("SHARED_LIB_DIR", "/root/shared")
        cmd = [sys.executable, "-B", os.path.join(HERE, "stock_record.py"), "--build"]
        if shutil.which("flock"):
            cmd = ["flock", "-n", "/tmp/stock_record.lock"] + cmd
        log = open(os.path.join(HERE, "stock_record.log"), "ab")
        subprocess.Popen(cmd, stdout=log, stderr=log, stdin=subprocess.DEVNULL, cwd=HERE, env=env, start_new_session=True, close_fds=True)
        return True
    except Exception as ex:                                   # noqa: BLE001
        print("stock_check: detached rebuild not started: %r" % (ex,), file=sys.stderr)
        return False


'''


def patch_check(s):
    a = s.index("def record(con):")
    b = s.index("# ------------------------------------------------------------------ the doors")
    s = s[:a] + NEW_RECORD + s[b:]
    s = once(s, 'VERSION = "1.1"                                             # v1.1: the cold review\'s points (data-item, since-moment, below-zero, cache, viewer, note)',
             'VERSION = "1.2"                                             # v1.2 S933: every figure from stock_record (the stock of record); v1.1: the cold review\'s points', "stock_check VERSION")
    s = once(s, "CACHE_SECONDS = 120", "CACHE_SECONDS = 60                                          # S933: the record itself is cached by its fingerprint; this only spares a double read", "stock_check CACHE")
    # the record's lines are already made: _lines_for is no longer read by record() -- kept, unlinked, one release (dead 1)
    return s


def patch_html(s):
    s = once(s, "  if(r.pieces)n.push('pieces');\n  return n.join(' · ');",
             "  if(r.pieces)n.push('pieces');\n  if(r.words)n.push(esc(r.words));\n  return n.join(' · ');", "html rowNote")
    s = once(s, "{h:'Marg',n:1,f:function(r){return '<td class=\"n\">'+esc(r.marg_t)+'</td>';}},",
             "{h:'Marg',n:1,f:function(r){return '<td class=\"n\">'+(r.state==='marg_behind'?'behind a bill':esc(r.marg_t))+'</td>';}},", "html marg cell")
    s = once(s, "  $('when').innerHTML='read '+esc(D.at.replace('T',' ').slice(0,16))+' IST'+(D.cached?' · <a href=\"/finance/stockcheck/?fresh=1\">read again</a>':'');",
             "  $('when').innerHTML='read '+esc(D.at.replace('T',' ').slice(0,16))+' IST · the record built '+esc((D.reports&&D.reports.built_at)||'—')+(D.record&&D.record.rebuilding?' · <b>being rebuilt now</b> — read again in a minute':'')+(D.cached?' · <a href=\"/finance/stockcheck/?fresh=1\">read again</a>':'');", "html when line")
    s = once(s, "  var look=R.filter(function(r){return r.gap!==null&&r.gap!==0;});",
             "  var look=R.filter(function(r){return (r.state==='look'||r.state==='waiting')&&r.gap!==null&&r.gap!==0;});\n"
             "  var behind=R.filter(function(r){return r.state==='marg_behind';}), cons=R.filter(function(r){return r.state==='consumable';});", "html look filter")
    s = once(s, "  h+='</div>';\n  // deliveries waiting",
             "  h+='</div>';\n"
             "  // Marg's figure behind a bill\n"
             "  if(behind.length){h+='<div class=\"card\" id=\"behind\"><h2>'+behind.length+' items where Marg\\'s figure is behind a bill</h2><div class=\"mute\">Marg\\'s figure would go below zero: a bill Marg holds is not in the record yet, or a bill is not keyed. No gap is judged until the purchase side is settled.</div>'+table(behind,LOOK)+'</div>';}\n"
             "  // the clinic's consumables\n"
             "  if(cons.length){h+='<div class=\"card\" id=\"cons\"><h2>'+cons.length+' clinic consumables</h2><div class=\"mute\">Used by the clinic without sale bills (your consumption list): shown, never judged as a shop difference.</div><details><summary>Show them</summary>'+table(cons,LOOK)+'</details></div>';}\n"
             "  // deliveries waiting", "html sections")
    s = once(s, "  var ag=R.filter(function(r){return r.gap===0;}), agIn=ag.filter(function(r){return r.marg>0;});",
             "  var ag=R.filter(function(r){return r.gap===0&&(r.state==='agree'||r.state==='waiting');}), agIn=ag.filter(function(r){return r.marg>0;});", "html agree filter")
    s = once(s, "  $('intro').innerHTML=\"Marg's closing of <b>\"+esc(D.reports.closing_as_on)+\"</b> (taken \"+esc(D.reports.closing_at)+\") against the shelf figure:",
             "  $('intro').innerHTML=\"Marg's closing of <b>\"+esc(D.reports.closing_as_on)+\"</b> (the report taken \"+esc(D.reports.closing_at)+(D.reports.kind_word?', '+esc(D.reports.kind_word):'')+\", plus the bills Amir keyed after it and the sales since) against the shelf figure:", "html intro")
    s = once(s, "  h+='<div class=\"card\"><h2>Reports behind this page</h2><div>Marg\\'s closing stock: as on '+esc(D.reports.closing_as_on)+', received '+esc(D.reports.closing_at)+(D.reports.start?' (a morning print: it stands for the end of the day before)':'')+' · Sale report: to '+esc(D.reports.sale_to||'—')+' · Purchases in Marg: to '+esc(D.reports.purchase_to||'—')+'</div>'\n"
             "    +'<div class=\"mute\" style=\"margin-top:4px\">Every figure here comes from the one stock function; the retired PC estimate is not on this page. The old Stock drift and Stock now addresses open this page.</div></div>';",
             "  h+='<div class=\"card\"><h2>Reports behind this page</h2><div>Marg\\'s closing stock: printed as on '+esc(D.reports.closing_printed)+', taken '+esc(D.reports.closing_at)+' — '+esc(D.reports.kind_word||'')+' · Sale report: to '+esc(D.reports.sale_to||'—')+' · Purchases in Marg: to '+esc(D.reports.purchase_to||'—')+'</div>'\n"
             "    +'<div class=\"mute\" style=\"margin-top:4px\">Every figure here is the stock of record (built '+esc(D.reports.built_at||'—')+'), the one record every page reads: Marg\\'s newest report, the bills keyed after it, the sales since, the last count carried forward, the deliveries waiting. '+(D.totals&&D.totals.late?D.totals.late+' items carry a bill keyed after the print. ':'')+'The old Stock drift and Stock now addresses open this page.</div></div>';", "html reports")
    return s


def patch_ledger(s):
    a = '''    last = sp.execute("SELECT as_on, units FROM sp_close WHERE k20=? ORDER BY as_on DESC LIMIT 1", (key,)).fetchone()
    A = arrived(con, sp, key)
    add = sum(a["units"] for a in A)
    hands_all = [h for h in HR if h["state"] == "bad"]
    bad_days = sorted({str(h["day_to"])[:10] for h in hands_all}, reverse=True)
    marg_txt = U.fmt(last[1]) if last else "—"
    exp_txt = U.fmt((float(last[1]) if last else 0.0) + add) if last else "—"
'''
    b = '''    last = sp.execute("SELECT as_on, units FROM sp_close WHERE k20=? ORDER BY as_on DESC LIMIT 1", (key,)).fetchone()
    A = arrived(con, sp, key)
    add = sum(a["units"] for a in A)
    hands_all = [h for h in HR if h["state"] == "bad"]
    bad_days = sorted({str(h["day_to"])[:10] for h in hands_all}, reverse=True)
    marg_txt = U.fmt(last[1]) if last else "—"
    exp_txt = U.fmt((float(last[1]) if last else 0.0) + add) if last else "—"
    rec, rec_sub, rec_exp = None, "", ""                     # S933: the head figures from THE STOCK OF RECORD (stock_record) when it has this item
    try:
        import stock_record as _SR                           # noqa: PLC0415 -- beside this file
        rec = _SR.row(con, key, sp=None, refresh="never")
        if rec is not None and rec.get("marg_units") is not None:
            MM = _SR.meta(con)
            marg_txt = U.fmt(float(rec["marg_units"]))
            bits = ["Marg's report of %s, the end of %s" % (dmon(MM.get("cap_as_on") or ""), dmon(MM.get("cap_end_day") or ""))]
            if rec.get("late"):
                bits.append("+ bill%s %s keyed after the print" % ("s" if len(rec["late"]) > 1 else "", ", ".join(str(c.get("bill")) for c in rec["late"])))
            if abs(float(rec.get("marg_after") or 0)) >= 0.5:
                bits.append("%s since" % U.fmt(float(rec["marg_after"]), sign=True))
            rec_sub = " · ".join(bits)
            wu = float(rec.get("waiting_units") or 0)
            exp_txt = U.fmt(float(rec["marg_units"]) + wu)
            rec_exp = ("Marg %s %s waiting, not yet in Marg" % (marg_txt, U.fmt(wu, sign=True))) if wu else "nothing arrived waits for Marg"
    except Exception as _e933:                               # noqa: BLE001 -- the head as before
        print("S933 record head failed: %r" % (_e933,), file=sys.stderr)
        rec = None
'''
    s = once(s, a, b, "ledger head figures")
    s = once(s, '''             esc(marg_txt), esc(("Marg's closing of %s" % dmon(last[0])) if last else "not in Marg's closings")),''',
             '''             esc(marg_txt), esc(rec_sub if rec is not None else (("Marg's closing of %s" % dmon(last[0])) if last else "not in Marg's closings"))),''', "ledger marg sub")
    s = once(s, '''             esc(exp_txt), esc(("Marg %s %s arrived, not yet in Marg" % (marg_txt, U.fmt(add, sign=True))) if add else
                 ("a waiting scan carries it but adds nothing — see below" if A else "nothing arrived waits for Marg"))),''',
             '''             esc(exp_txt), esc(rec_exp if rec is not None else (("Marg %s %s arrived, not yet in Marg" % (marg_txt, U.fmt(add, sign=True))) if add else
                 ("a waiting scan carries it but adds nothing — see below" if A else "nothing arrived waits for Marg")))),''', "ledger expected sub")
    return s


def main():
    src, dst = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    f = os.path.join(src, "stock_figure.py")
    if md5(f) != FROM_MD5["stock_figure"]:
        sys.exit("stock_figure.py FROM md5 %s is not %s (S928's live file) -- read the live file whole before patching" % (md5(f), FROM_MD5["stock_figure"]))
    wr(os.path.join(dst, "stock_figure.py"), patch_figure(rd(f)))
    wr(os.path.join(dst, "stock_check.py"), patch_check(rd(os.path.join(src, "stock_check.py"))))
    wr(os.path.join(dst, "stock_check.html"), patch_html(rd(os.path.join(src, "stock_check.html"))))
    wr(os.path.join(dst, "item_ledger.py"), patch_ledger(rd(os.path.join(src, "item_ledger.py"))))
    for n in ("stock_figure.py", "stock_check.py", "stock_check.html", "item_ledger.py"):
        print("%s  %s" % (md5(os.path.join(dst, n)), n))


if __name__ == "__main__":
    main()
