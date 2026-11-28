#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  stock_check.py  ·  v1.0  ·  kit S930_STOCK_CHECK_PAGE  ·  Session 503 (Sanjeevni)  ·  22-Nov-2026
#
#  THE OWNER'S STOCK CHECK PAGE -- Marg against the shelf, to his mock-up v5 (https://claude.ai/artifact/XzqcBUHoroPyTt7xG8bNea, D1037):
#  one page in place of Stock drift and Stock now (their addresses send here), every figure from THE one stock function (stock_figure):
#  Marg's figure on the newest usable closing capture, the shelf figure (the last count carried forward through Marg's own sales, purchases
#  and vouchers), the deliveries Marg has not got yet (by the scanned bill's quantity, never reception's tap -- S928), each item ONCE under
#  Marg's current name (a count under an old spelling is read through the rename memory, F-1563). Darpan's counts (every one, newest first,
#  with what the system judged), 'Count this' on every row and in one box (stock_watch.ask: the head of his next list), the items Marg holds
#  with no shelf figure yet, the count names Marg no longer prints, the items that agree, the reports behind the page.
#  Mounted by sanjeevni_day.init (as hub_panels). Roles as the drift page had them (checker and above). English, PC first, no dialogs.
#  Quantities in strips:tabs ('16:3'); pieces for orthotics, gels and sachets; a plus is more on the shelf than in Marg, a minus is less.
#  v1.5 S965 (26-Nov, D1083 D1086): /api/vouchers -- Marg's Stock Issue / Stock Receive lines judged against every correction asked of Amir
#  (voucher_judge.page); the page draws the two boxes and the tags from it. A cut name that fits several items asks the one-item registers.
#  v1.6 S967 (27-Nov, kit A1 of S534_FINAL_BUILD_PLAN; his 'ok' 09:25 on mock-up v9, D1090 D1091 D1092): /api/desk -- THE ONE PAGE's five
#  boxes, READ ONLY: 1 short in a fresh count (and the group within the allowance) . 2 on its way to Marg . 3 old corrections re-judged on
#  the whole item . 4 vouchers nobody asked for (history until his rule date) . settled in Marg; every row with its path, its voucher lines
#  and its item ledger (the ledger's own /api/fold). Write off / Pursue are kit A2: nothing on this door writes.
#  v1.7 S969 (27-Nov, kit A2 of S534_FINAL_BUILD_PLAN, D1090 D1092): THE DESK'S WRITES -- his two taps each, no dialog (18-Nov rule), on
#  POST /api/desk/act (the owner only): Write off (one Stock Issue line per item on Amir's card, kind 'tap' in the S957 word shape; the
#  day's write-offs are ONE card, one voucher, one 'Kar diya'; a card Amir has tapped done never grows -- the next write-off starts a new
#  card; the batch only SUGGESTED from Marg's last Batch Stock report) . Pursue (a recount at the head of Darpan's next list; the row
#  comes back with BOTH counts, or closes by itself when the recount agrees with Marg) . the allowance group's button . the old counts
#  that differ from Marg onto Darpan's next list (F-1712). Every write builds the desk afresh first and acts only on a row the desk
#  offers that button on (nothing on an evening count still waiting for its sales). Its own table: stock_desk_action.
import datetime as dt
import html as _html
import io
import os
import re
import sqlite3
import sys
import time

from flask import Blueprint, jsonify, redirect, request

VERSION = "1.8"                                             # v1.8 S971: Amir by himself (claims, the inquiry, settings, the loss register); v1.7 S969: the desk's writes (/api/desk/act); v1.6 S967: /api/desk (the one page, read only); v1.5 S965: /api/vouchers
VERSION_S934 = "1.4"                                             # v1.3 S934: Count now / Next list, withdraw, a count placed to its bill; v1.2 S933: every figure from stock_record (the stock of record); v1.1: the cold review's points
KIT = "S930_STOCK_CHECK_PAGE"
HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "stock_check.html")
RETIRED = ("/finance/stock/page/drift", "/finance/stock/page/now")     # the retired pages: their addresses send here (D1037, 13 pages to 5)
HOME = "/finance/stockcheck/"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
bp = Blueprint("stock_check", __name__, url_prefix="/finance/stockcheck")
_db = _require = None
_unit = "medical"


def init(app, db_getter, require_fn, unit="medical"):
    global _db, _require, _unit
    _db, _require, _unit = db_getter, require_fn, unit
    app.register_blueprint(bp)

    @app.before_request
    def _s930_retired():                                     # the two retired addresses: one page now (their code stays, unlinked)
        if request.path.rstrip("/") in RETIRED:
            return redirect(HOME, code=302)
        return None
    print("S930 stock_check mounted v%s" % VERSION, file=sys.stderr, flush=True)   # the service log proves the mount (F-1554)
    return bp


def esc(s):
    return _html.escape(str(s if s is not None else ""), quote=True)


def _SW():
    import stock_watch                                        # noqa: PLC0415 -- beside this file
    return stock_watch


def _SF():
    import stock_figure                                       # noqa: PLC0415
    return stock_figure


def now_ist():
    return dt.datetime.now(IST).replace(microsecond=0, tzinfo=None).isoformat()


def today():
    return dt.datetime.now(IST).date()


def _has(con, t):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone() is not None


def norm(s):
    return re.sub(r"\s+", " ", str(s or "").strip().upper())


def st(units, pack, signed=False):
    """'16:3' strips:tabs for a packed item, '25' pieces for pack 1; None -> '—'. signed: '+1:4' / '−2:12' / '0'."""
    if units is None:
        return "—"
    try:
        v = int(round(float(units)))
    except (TypeError, ValueError):
        return "—"
    p = int(pack or 1)
    neg = v < 0
    a = abs(v)
    body = ("%d:%d" % (a // p, a % p)) if p > 1 else "%d" % a
    if neg:
        return "−" + body
    if signed and v > 0:
        return "+" + body
    return body


def dmy(iso):
    s = str(iso or "")[:10]
    return "%s-%s-%s" % (s[8:10], s[5:7], s[0:4]) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s) else s


def stamp(ts):
    s = str(ts or "").strip()
    return "%s %s IST" % (dmy(s[:10]), s[11:16]) if (len(s) >= 16 and s[10] in ("T", " ")) else dmy(s)


def day_word(iso):
    s = str(iso or "")[:10]
    try:
        d = dt.date.fromisoformat(s)
    except ValueError:
        return dmy(s)
    return "%s %s" % (("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")[d.weekday()], "%s-%s" % (s[8:10], s[5:7]))


# ------------------------------------------------------------------ the record
def _ortho(con):
    try:
        return {norm(r[0]) for r in con.execute("SELECT item FROM stock_item_section WHERE section='Orthotics'")} if _has(con, "stock_item_section") else set()
    except sqlite3.Error:
        return set()


def _lines_for(con, sp, SF, SW, name, since_at, ctx, base_kind="count"):
    """The arrival lines that COUNT for an item (not carried, not expired), each with the bill's word (S928.bill_units) -- the 'deliveries
    waiting for Marg' table's rows."""
    out = []
    try:
        lines = [a for a in SW._arrivals(con, name, str(since_at or ""), sp, ctx=ctx) if not str(a.get("billed_bill_no") or "").strip()]
        lines += SF.scan_lines(con, sp, name, (str(since_at or "")[:10] if base_kind == "count" else str(since_at or "")), ctx)   # as S928 A5b
    except Exception:                                         # noqa: BLE001
        return out
    seen = set()
    for a in lines:
        if a.get("line_id") in seen:
            continue
        seen.add(a.get("line_id"))
        try:
            if SF.carried(con, sp, a, ctx) is not None or SF.expired(con, sp, a, ctx):
                continue
        except Exception:                                     # noqa: BLE001
            continue
        b = SF.bill_units(con, sp, a, ctx) if hasattr(SF, "bill_units") else None
        tap = float(a.get("units") or 0)
        units = (float(b["units"]) if (b is not None and b.get("units") is not None) else tap)
        ps = int(a.get("pack_size") or 1)
        word, short = "", 0.0
        if b is None or b.get("units") is None:
            word = ("tapped %s, no bill read yet" % st(tap, ps)) if a.get("kind") != "scan" else ("the scan is tied, the quantity not read yet")
        elif not b.get("on_bill"):
            word, short = "tapped %s, NOT on the bill — counts nothing" % st(tap, ps), -tap
        elif abs(float(b["units"]) - tap) < 0.5:
            word = "tap %s = bill" % st(tap, ps)
        elif float(b["units"]) < tap:
            word, short = "tapped %s, bill %s — %s short, back on %s's next order" % (st(tap, ps), st(b["units"], ps), st(tap - float(b["units"]), ps), (a.get("vendor") or "the dealer").split()[0]), float(b["units"]) - tap
        else:
            word = "tapped %s, bill %s — %s over the order" % (st(tap, ps), st(b["units"], ps), st(float(b["units"]) - tap, ps))
        out.append(dict(line_id=a.get("line_id"), vendor=a.get("vendor") or "", kind=a.get("kind") or "tap", at=str(a.get("arrived_at") or a.get("scan_at") or "")[:16],
                        units=units, tap=tap, bill=(float(b["units"]) if (b and b.get("units") is not None) else None), scan_id=(b or {}).get("scan_id"),
                        stamp=(("B-%s" % (b or {}).get("scan_id")) if (b or {}).get("scan_id") else ""), word=word, short=short, pack=ps))
    return out


def _note_word(note):
    """A point's note for the owner's page: Darpan's own free text (a gadbad) is not shown, only that he flagged something."""
    n = str(note or "").strip()
    if not n:
        return ""
    if n.lower().startswith("gadbad"):
        return "Darpan flagged something -- see the trace"
    return n[:120]


_CACHE = dict(at=0.0, rec=None)
CACHE_SECONDS = 60                                          # S933: the record itself is cached by its fingerprint; this only spares a double read


def record_cached(con, fresh=False):
    """record(con) at most once in CACHE_SECONDS (the page rebuilds every item from the one stock function); ?fresh=1 or a Count rebuilds it."""
    now = time.monotonic()
    if not fresh and _CACHE["rec"] is not None and now - _CACHE["at"] < CACHE_SECONDS:
        rec = dict(_CACHE["rec"])
        rec["cached"] = True
        return rec
    rec = record(con)
    if rec.get("ok"):
        _CACHE["rec"], _CACHE["at"] = rec, now
    rec["cached"] = False
    return rec


def record(con):
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
        try:
            SW._s934_settle(con, sp)                          # S934: a Count now judged to its bill once its day's sales are in
        except Exception:                                     # noqa: BLE001
            pass
        if _has(con, "stock_spot_roster"):
            for pid, reason in con.execute("SELECT point_id, reason FROM stock_spot_roster WHERE point_id IS NOT NULL"):
                asked[int(pid)] = reason or ""
        jw_col = "judge_words" if "judge_words" in {r[1] for r in con.execute("PRAGMA table_info(stock_point)")} else "NULL"   # S952: the judgment's words
        for pid, item, at, q, e, g, basis, by, note, status, jw in con.execute(
                "SELECT id, item, at, qty_units, expected_units, gap_units, basis, by, note, status, %s FROM stock_point WHERE source IN ('spot','darpan') "
                "AND COALESCE(status,'')<>'superseded' ORDER BY at DESC, id DESC" % jw_col):
            if str(at)[:10] < lo:
                older += 1
                continue
            pack = SF.pack_of(con, sp, item, ctx)[0]
            reason = asked.get(int(pid), "")
            counts.append(dict(id=pid, item=item, key=SF.key_of(sp, item, ctx), at=str(at)[:16], day=day_word(at), time=str(at)[11:16], qty_t=st(q, pack),
                               expected_t=(st(e, pack) if e is not None else "—"), gap_t=(st(g, pack, signed=True) if g is not None else "—"), gap=g, basis=basis or "",
                               by=(by or "").title(), asked=("you asked" in reason.lower()), reason=reason, note=(" · ".join(x for x in (str(jw or "").strip(), _note_word(note)) if x)[:400]), provisional=(status == "provisional"),   # S952
                               awaits=(status == "awaits_sales"),                      # S934
                               evening=(not str(note or "").startswith("Count now, to bill")) and SF.evening_count(at, S.get("evening_hour", 17), str(at)[:10]) if hasattr(SF, "evening_count") else False))   # S934: a bill-placed count is never 'the end of its day'
    except sqlite3.Error:
        pass
    # the next list: his asks first, then the system's picks
    nxt, asks = [], []
    try:
        nd = SW.next_roster_day(S, None, con) if getattr(SW, "_s958_asks_waiting", None) else SW.next_roster_day(S)   # S958
        if nd is not None:
            nxt = [dict(item=x["item"], reason=x.get("reason") or "") for x in SW.preview_roster(con, nd, S, sp)][:12]
        try:                                                  # S934: each ask with its id and mode (now | next), withdrawable
            asks = [dict(id=r[3], item=r[0], at=stamp(r[1]), by=(r[2] or "").title(), mode=r[4]) for r in
                    con.execute("SELECT item, at, by, id, COALESCE(mode,'next') FROM stock_watch_ask WHERE done_at IS NULL ORDER BY id")]
        except sqlite3.Error:
            asks = [dict(id=r[3], item=r[0], at=stamp(r[1]), by=(r[2] or "").title(), mode="next") for r in
                    con.execute("SELECT item, at, by, id FROM stock_watch_ask WHERE done_at IS NULL ORDER BY id")]
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


# ------------------------------------------------------------------ the doors
@bp.route("/")
def r_page():
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    try:
        with io.open(PAGE, "r", encoding="utf-8") as fh:
            t = fh.read()
    except OSError:
        return jsonify(ok=False, error="template_missing", message="stock_check.html is not beside stock_check.py"), 503
    return t, 200, {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store"}


@bp.route("/api/rows")
def r_rows():
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    try:
        return jsonify(record_cached(con, fresh=str(request.args.get("fresh") or "") in ("1", "yes")))
    except Exception as e:                                    # noqa: BLE001
        return jsonify(ok=False, reason="The page could not be built: %s" % type(e).__name__, rows=[], counts=[]), 200


@bp.route("/api/count", methods=["POST"])
def r_count():
    """Count this -- S934: {item, mode: 'now' | 'next'} -- now: Darpan's screen at once; next: the head of his next morning list (stock_watch.ask)."""
    u, err = _require("checker", "maker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    item = re.sub(r"\s+", " ", str(b.get("item") or "")).strip()[:80]
    if not item:
        return jsonify(ok=False, message="Name the item."), 400
    con = _db()
    SW = _SW()
    mode = str(b.get("mode") or "").strip().lower()                                    # S934: now | next | (none: an open ask is never moved)
    mode = mode if mode in ("now", "next") else None
    ok, msg, code = SW.ask(con, item, (u or {}).get("user") or "", sp=SW.Spine(), mode=mode)
    if ok:
        _CACHE["rec"] = None                                 # the next list moved: the page rebuilds on its next read
    return jsonify(ok=ok, message=msg), code


@bp.route("/api/withdraw", methods=["POST"])
def r_withdraw():
    """S934: withdraw one of his open asks {ask_id} (stock_watch.withdraw_ask)."""
    u, err = _require("checker", "maker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    con = _db()
    ok, msg, code = _SW().withdraw_ask(con, b.get("ask_id"), (u or {}).get("user") or "")
    if ok:
        _CACHE["rec"] = None
    return jsonify(ok=ok, message=msg), code


_VCACHE = dict(at=0.0, v=None)


@bp.route("/api/vouchers")
def r_vouchers():
    """S965: Marg's stock vouchers judged (voucher_judge.page), at most once in CACHE_SECONDS. A cut name that fits several items: the
    one-item Stock Registers asked on his list (voucher_judge.ask_registers -- an ask already made is never made twice)."""
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    now = time.monotonic()
    if _VCACHE["v"] is not None and now - _VCACHE["at"] < CACHE_SECONDS and str(request.args.get("fresh") or "") not in ("1", "yes"):
        return jsonify(_VCACHE["v"])
    con = _db()
    try:
        import voucher_judge as VJ                            # noqa: PLC0415 -- beside this file
        v = VJ.page(con, today().isoformat())
        if v.get("ok") and v.get("cut") and not _require("checker", "maker")[1]:   # a viewer's read never writes (review S8)
            try:
                v["asked"] = VJ.ask_registers(con)
            except Exception:                                 # noqa: BLE001
                v["asked"] = 0
        if v.get("ok"):
            _VCACHE["v"], _VCACHE["at"] = v, now
        return jsonify(v)
    except Exception as e:                                    # noqa: BLE001
        return jsonify(ok=False, reason="The vouchers could not be read: %s" % type(e).__name__), 200


# ------------------------------------------------------------------ S967: the one page's boxes (read only)
_DCACHE = dict(at=0.0, v=None)
FRESH_DAYS = 30                                             # a short is a fresh count's only within this many days
RULE_DATE_KEY = "stock.voucher_rule_from"                   # the day from which a voucher nobody asked for starts the inquiry (kit B sets it)
LEDGER_FOLD = "/finance/sanjeevni/ledger/api/fold"


def _setting(con, key):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        return r[0] if r else None
    except sqlite3.Error:
        return None


def _point_at(con, item, at):
    """The count a record row stands on (its base_at): dict(id, at, qty, expected, gap, status, note, words, last_bill) or None."""
    try:
        cols = {r[1] for r in con.execute("PRAGMA table_info(stock_point)")}
        jw = "judge_words" if "judge_words" in cols else "NULL"
        lb = "last_bill" if "last_bill" in cols else "NULL"
        r = con.execute("SELECT id, at, qty_units, expected_units, gap_units, status, note, %s, %s, source FROM stock_point WHERE item=? AND substr(at,1,16)=substr(?,1,16) "
                        "AND COALESCE(status,'')<>'superseded' ORDER BY id DESC LIMIT 1" % (jw, lb), (item, str(at or "").replace(" ", "T"))).fetchone()
    except sqlite3.Error:
        return None
    if not r:
        return None
    return dict(id=r[0], at=str(r[1]), qty=r[2], expected=r[3], gap=r[4], status=str(r[5] or ""), note=str(r[6] or ""), words=str(r[7] or ""),
                last_bill=r[8], source=str(r[9] or ""))


def _allowance(con, item, pack, P):
    """The allowance the count's own judgment used (record_judges.settle_words): stock.allowance_pct % of the item's sales since the count
    before it, to the figure's day, at least stock.allowance_min_strips strips. None when the stock record (the spine) cannot be read."""
    try:
        import record_judges as RJ                            # noqa: PLC0415 -- beside this file
        sp = _SW().Spine()
        if not getattr(sp, "ok", False):
            return None
        SW, SF = _SW(), _SF()
        at = str(P["at"]).replace(" ", "T")[:19]
        r = con.execute("SELECT at FROM stock_point WHERE item_norm=? AND at<? AND COALESCE(status,'') NOT IN ('superseded') AND COALESCE(id,-1)<>? ORDER BY at DESC LIMIT 1",
                        (SW.norm_name(item), at, int(P["id"]))).fetchone()   # review M1: stock_watch's own name form, as settle_words reads it
        D = at[:10]
        since = str(r[0])[:10] if r else (dt.date.fromisoformat(D) - dt.timedelta(days=30)).isoformat()
        N = SW._s934_bill_no(P["last_bill"]) if P.get("last_bill") else None          # record_judges.judge's own rule for the figure's day
        sales_in = SW._s934_sales_in(con, sp, D)
        ev = (N is None) and SF.evening_count(at, int(SW.settings(con).get("evening_hour", 17)), D)
        as_on = D if ((N is not None or ev) and sales_in) else (dt.date.fromisoformat(D) - dt.timedelta(days=1)).isoformat()
        return int(RJ._allow(con, sp, item, pack, since, as_on))
    except Exception:                                         # noqa: BLE001
        return None


def _vlines_for(VJ, con, item, J):
    """The item's Marg voucher lines (voucher_judge.item_lines), each with its voucher's every line."""
    try:
        return VJ.item_lines(con, [item], J)[0] if (J and J.get("ok")) else []
    except Exception:                                         # noqa: BLE001
        return []


def _VI():
    """S971: Amir by himself (voucher_inquiry.py, beside this file)."""
    import voucher_inquiry                                    # noqa: PLC0415
    return voucher_inquiry


# ------------------------------------------------------------------ S969: the desk's writes (kit A2) -- their own table and helpers
KIT_S969 = "S969_STOCKCHECK_DESK_WRITES"
KIT_S971 = "S971_AMIR_BY_HIMSELF"
WO_KEY = "S969:wo:"                                         # amir_job key: S969:wo:<day>:<card>:<item> -- one card a day, a done card never grows
DESK_DDL = ("CREATE TABLE IF NOT EXISTS stock_desk_action (id INTEGER PRIMARY KEY, kind TEXT NOT NULL, item TEXT NOT NULL, item_norm TEXT NOT NULL, "
            "pack INTEGER, units INTEGER, point_id INTEGER, point_at TEXT, qty_units REAL, expected_units REAL, batch TEXT, job_key TEXT, "
            "ask_id INTEGER, box TEXT, day TEXT NOT NULL, at TEXT NOT NULL, by TEXT, note TEXT)")


def _ensure_desk(con):
    con.execute(DESK_DDL)
    try:                                                      # S971: the value of a write-off, frozen at the tap (the loss register)
        _VI().ensure_value_cols(con)
    except Exception:                                         # noqa: BLE001
        pass
    con.execute("CREATE INDEX IF NOT EXISTS ix_s969_item ON stock_desk_action (item_norm, kind)")
    con.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_s969_job ON stock_desk_action (job_key) WHERE job_key IS NOT NULL")


def _pursues(con):
    """{norm(item): his newest Pursue} -- dict(at, point_id, point_at, qty, expected, short, pack). {} before the first."""
    if not _has(con, "stock_desk_action"):
        return {}
    out = {}
    try:
        for item, at, pid, pat, q, e, u, pk in con.execute("SELECT item, at, point_id, point_at, qty_units, expected_units, units, pack FROM stock_desk_action "
                                                           "WHERE kind='pursue' ORDER BY at, id"):
            out[norm(item)] = dict(at=str(at or ""), point_id=pid, point_at=str(pat or ""), qty=q, expected=e, short=u, pack=pk)
    except sqlite3.Error:
        return {}
    return out


def _first_count_after(con, item, at):
    """(id, at) of the FIRST count of the item after `at` (Darpan's or a spot morning's, not replaced) -- the one count that answers his
    Pursue (review 4: a later count never does); None when none yet."""
    try:
        r = con.execute("SELECT id, at FROM stock_point WHERE item_norm=? AND at>? AND source IN ('spot','darpan') "
                        "AND COALESCE(status,'') NOT IN ('superseded','recount','recounted') "     # second look 3: stock_watch's own rule
                        "ORDER BY at, id LIMIT 1", (_SW().norm_name(item), str(at or ""))).fetchone()
        return (int(r[0]), str(r[1])) if r else None
    except sqlite3.Error:
        return None


def _pz_resolve(con, pz):
    """Second look 2: Darpan corrected the pursued count ('Galat likha? Badlo' -- the old point superseded, its note 'ab point N'): the
    replacement is the pursued count, and only a count after IT answers the Pursue. -> (point id, moment after which a count answers)."""
    pid, after = pz.get("point_id"), pz["at"]
    for _i in range(4):
        try:
            r = con.execute("SELECT status, note FROM stock_point WHERE id=?", (int(pid or -1),)).fetchone()
        except sqlite3.Error:
            break
        m = re.search(r"ab point (\d+)", str((r or ("", ""))[1] or "")) if r and r[0] == "superseded" else None
        if not m:
            break
        pid = int(m.group(1))
        n = con.execute("SELECT at FROM stock_point WHERE id=?", (pid,)).fetchone()
        after = max(after, str(n[0] if n else ""))
    return pid, after


def _wo_points(con):
    """The counts already written off from the desk (second look 4: such a row waits for Marg's figure, no button)."""
    if not _has(con, "stock_desk_action"):
        return set()
    try:
        return {int(r[0]) for r in con.execute("SELECT point_id FROM stock_desk_action WHERE kind='writeoff' AND point_id IS NOT NULL")}
    except sqlite3.Error:
        return set()


def _can_write():
    """Second look 6: the buttons are drawn only for the owner (role checker); the door refuses anyone else anyway."""
    try:
        return not _require("checker")[1]
    except Exception:                                         # noqa: BLE001
        return False


def _ask_open(con, ask_id, item):
    """True while his Pursue's ask is still open on Darpan's lists (review 5: a withdrawn or closed ask gives the buttons back)."""
    try:
        if ask_id:
            return con.execute("SELECT 1 FROM stock_watch_ask WHERE id=? AND done_at IS NULL", (int(ask_id),)).fetchone() is not None
        return con.execute("SELECT 1 FROM stock_watch_ask WHERE item_norm=? AND done_at IS NULL LIMIT 1", (_SW().norm_name(item),)).fetchone() is not None
    except sqlite3.Error:
        return False


def _pz_path(pz, P, pack):
    """Both counts, for a row he pursued: the first count, his Pursue, the recount."""
    out = [["ok", "First count %s: %s counted, Marg %s at the time -- %s short." % (dmy(pz["point_at"]), st(pz.get("qty"), pack), st(pz.get("expected"), pack),
                                                                                    st(pz.get("short"), pack))],
           ["ok", "You pursued it %s: a recount at the head of Darpan's next list." % stamp(pz["at"])]]
    if P:
        out.append(["ok", "Darpan's recount %s: %s counted, Marg %s at the time." % (dmy(P["at"]), st(P.get("qty"), pack), st(P.get("expected"), pack))])
    return out


def _open_asks(con):
    """{stock_watch name form: the day it was asked} of every count still open on Darpan's lists."""
    try:
        return {r[0]: str(r[1] or "")[:10] for r in con.execute("SELECT item_norm, MIN(at) FROM stock_watch_ask WHERE done_at IS NULL GROUP BY item_norm")}
    except sqlite3.Error:
        return {}


def _batch_hint(con, R, units):
    """The batch SUGGESTED for a write-off: Marg's last Batch Stock report (stock_batch_now), nearest expiry first, until the units are covered
    (at most two). (text, report day) or ('', '')."""
    if not _has(con, "stock_batch_now"):
        return "", ""
    try:
        r = con.execute("SELECT MAX(run_id) FROM stock_batch_now").fetchone()
        if not r or r[0] is None:
            return "", ""
        rows = con.execute("SELECT batch, expiry, units, as_on FROM stock_batch_now WHERE run_id=? AND (k20=? OR item=?) AND COALESCE(units,0)>0 "
                           "ORDER BY COALESCE(NULLIF(expiry,''),'9999'), batch", (r[0], (R.get("k20") or R["item"])[:20], R["item"])).fetchall()
    except sqlite3.Error:
        return "", ""
    pick, have = [], 0
    for b, _e, u, _a in rows:
        if not str(b or "").strip():
            continue
        pick.append(str(b).strip())
        have += int(u or 0)
        if have >= units or len(pick) == 2:
            break
    return (", phir ".join(pick), (str(rows[0][3] or "")[:10] if rows else "")) if pick else ("", "")


def _write_off(con, rows, who, box):
    """Write off: one Stock Issue line per item on Amir's card (amir_job kind 'tap', the S957 word shape the voucher judge reads; units from this
    table). The day's write-offs ride ONE card; a card Amir has tapped done never grows (the next write-off opens the day's next card).
    An item already written off and not yet done is never written twice. -> (made [item], skipped [item])."""
    SW = _SW()
    sp = SW.Spine()
    day, now = today().isoformat(), now_ist()
    ts = now.replace("T", " ")
    made, skipped = [], []
    _ensure_desk(con)
    con.commit()
    con.execute("BEGIN IMMEDIATE")                            # one writer: two quick taps never make two cards
    try:
        nums = {}
        for key, d, s in con.execute("SELECT key, done_at, said_at FROM amir_job WHERE key LIKE ?", (WO_KEY + day + ":%",)).fetchall():
            try:
                nums.setdefault(int(str(key).split(":")[3]), []).append(bool(d or s))
            except (IndexError, ValueError):
                continue
        card = 1
        if nums:
            top = max(nums)
            card = top + 1 if any(nums[top]) else top          # a card he has tapped done (any line of it) never grows
        for r in rows:
            item, inorm = r["item"], norm(r["item"])
            u, pack = int(r.get("short") or 0), int(r.get("pack") or 1) or 1
            if u <= 0:
                skipped.append(item)
                continue
            if con.execute("SELECT 1 FROM stock_desk_action d JOIN amir_job a ON a.key=d.job_key WHERE d.item_norm=? AND d.kind='writeoff' "
                           "AND a.done_at IS NULL", (inorm,)).fetchone():
                skipped.append(item)
                continue
            if r.get("pid") and con.execute("SELECT 1 FROM stock_desk_action WHERE kind='writeoff' AND point_id=?", (int(r["pid"]),)).fetchone():
                skipped.append(item)                          # review 3: one write-off per count, ever
                continue
            try:
                packing = (SW.item_info(con, sp, item) or {}).get("packing") or ""
            except Exception:                                 # noqa: BLE001
                packing = ""
            q_hi = SW.qw(u, pack, packing, item, "hi")
            key = "%s%s:%d:%s" % (WO_KEY, day, card, re.sub(r"[^A-Z0-9]+", "-", inorm).strip("-")[:40] or "item")
            base, n_ = key, 1
            while con.execute("SELECT 1 FROM amir_job WHERE key=?", (key,)).fetchone():   # review 8: never a clash
                n_ += 1
                key = "%s-%d" % (base, n_)
            b, b_on = _batch_hint(con, dict(item=item, k20=r.get("key") or ""), u)
            sub = ("Batch: %s (pichhli batch report %s ke hisaab se) — Marg mein jis batch mein maal ho, wahi lijiye." % (b, dmy(b_on))) if b else ""
            try:                                              # S971: the loss register's value, frozen at the tap
                cost_p, mrp_p = _VI().value_of(con, item, u, pack)
            except Exception:                                 # noqa: BLE001
                cost_p = mrp_p = None
            con.execute("INSERT INTO amir_job (key, kind, subject, text_hi, sub_hi, created_at, created_by, show_from) VALUES (?,?,?,?,?,?,?,?)",
                        (key, "tap", item, "%s — Marg mein STOCK ISSUE kijiye: %s" % (item, q_hi), sub, ts, "S969 (the owner's Write off, %s)" % ts[:16], ts))
            con.execute("INSERT INTO stock_desk_action (kind, item, item_norm, pack, units, point_id, point_at, qty_units, expected_units, batch, job_key, "
                        "box, day, at, by, cost_p, mrp_p, priced) VALUES ('writeoff',?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'at the tap')",
                        (item, inorm, pack, u, r.get("pid"), r.get("pat"), r.get("qty"), r.get("expected"), b, key, box, day, now, who, cost_p, mrp_p))
            SW._audit(con, "s969_writeoff", dict(item=item, units=u, pack=pack, key=key, card=card, box=box), who)
            made.append(item)
        con.commit()
    except Exception:
        con.rollback()
        raise
    return made, skipped


def _pursue(con, r, who):
    """Pursue: a recount at the head of Darpan's next list (stock_watch.ask with mode None: a new ask goes on the next list, an open one is
    never moved), and his Pursue kept with the count it questions. -> (ok, message)."""
    SW = _SW()
    ok_, msg, _code = SW.ask(con, r["item"], who, sp=SW.Spine(), mode=None)
    if not ok_:
        return False, msg
    _ensure_desk(con)
    a = con.execute("SELECT id FROM stock_watch_ask WHERE item_norm=? AND done_at IS NULL ORDER BY id DESC LIMIT 1", (SW.norm_name(r["item"]),)).fetchone()
    con.execute("INSERT INTO stock_desk_action (kind, item, item_norm, pack, units, point_id, point_at, qty_units, expected_units, ask_id, box, day, at, by) "
                "VALUES ('pursue',?,?,?,?,?,?,?,?,?,?,?,?,?)", (r["item"], norm(r["item"]), int(r.get("pack") or 1), int(r.get("short") or 0), r.get("pid"),
                                                               r.get("pat"), r.get("qty"), r.get("expected"), (a[0] if a else None), "short", today().isoformat(), now_ist(), who))
    SW._audit(con, "s969_pursue", dict(item=r["item"], point_id=r.get("pid"), ask_id=(a[0] if a else None)), who)
    con.commit()
    return True, msg


def _next_list(con, rows, who):
    """F-1712: the old counts that differ from Marg, onto Darpan's next list (stock_watch.ask, mode None). -> [item put]."""
    SW = _SW()
    sp = SW.Spine()
    put = []
    for r in rows:
        ok_, _m, _c = SW.ask(con, r["item"], who, sp=sp, mode=None)
        if ok_:
            put.append(r["item"])
    if put:
        _ensure_desk(con)
        for it in put:
            con.execute("INSERT INTO stock_desk_action (kind, item, item_norm, box, day, at, by) VALUES ('nextlist',?,?,'recount',?,?,?)",
                        (it, norm(it), today().isoformat(), now_ist(), who))
        con.commit()
    return put


def desk(con, day=None):
    """THE ONE PAGE (mock-up v9): the five boxes, read only. Every figure from the stock of record (stock_of_record), the counts
    (stock_point) and the voucher judge. {ok, box1, allow, way, old, moves, settled, settings, totals, at}."""
    import voucher_judge as VJ                                # noqa: PLC0415 -- beside this file
    day = day or today().isoformat()
    RR = VJ.record_rows(con)
    if not RR:
        return dict(ok=False, reason="The stock of record is not built yet: the boxes have nothing to judge.")
    try:
        J = VJ.judge(con, day)
    except Exception:                                         # noqa: BLE001
        J = dict(ok=False, asks=[], lines=[], vouchers=[])
    A = J.get("asks") or []
    lo = (dt.date.fromisoformat(day) - dt.timedelta(days=FRESH_DAYS)).isoformat()
    open_by_item = {}
    for a in A:                                               # an open ask that moves the item's TOTAL (a count line or Amir's card; a batch fix moves none)
        if a.get("state") in VJ.WAY_STATES + ("not_in_marg",) and a.get("src") in ("count", "job"):
            R = VJ.record_for(RR, set(a.get("forms") or {norm(a["item"])}))
            open_by_item.setdefault(norm(R["item"]) if R else norm(a["item"]), []).append(a)

    def row(R, **kw):
        pack = int(R.get("pack") or 1) or 1
        d = dict(item=R["item"], key=R.get("k20") or "", pack=pack, marg_t=st(R.get("marg_units"), pack), shelf_t=st(R.get("shelf_units"), pack),
                 gap_t=(st(R.get("gap_units"), pack, signed=True) if R.get("gap_units") is not None else "—"), base=dmy(R.get("base_day")),
                 base_kind=R.get("base_kind") or "", vlines=_vlines_for(VJ, con, R["item"], J), path=[], tags=[])
        d.update(kw)
        return d
    box1, allow, way, settled, noted = [], [], [], [], []
    PZ = _pursues(con)                                        # S969: his Pursue taps, the newest per item
    WOP = _wo_points(con)                                     # S969: the counts already written off
    # 1 · short in a fresh count (the record stands on a spot / Darpan count of the last 30 days, and Marg holds more)
    for k, R in sorted(RR.items()):
        if R.get("base_kind") not in ("spot", "darpan") or "old_base" in str(R.get("marg_flag") or ""):
            continue
        if str(R.get("base_day") or "") < lo:
            continue
        g = R.get("gap_units")
        P = _point_at(con, R["item"], R.get("base_at"))
        pack = int(R.get("pack") or 1) or 1
        if g is None:
            continue
        pz, pz_state = PZ.get(norm(R["item"])), ""            # S969: answered (the first count since his Pursue) . waiting . catching (counted, the record not yet)
        if pz and P:
            pz_pid, pz_after = _pz_resolve(con, pz)
            fc = _first_count_after(con, R["item"], pz_after)
            if fc is None:
                if int(P["id"]) == int(pz_pid or -1) and _ask_open(con, pz.get("ask_id"), R["item"]):
                    pz_state = "waiting"                      # (review 5) a withdrawn ask: the buttons come back
            elif int(P["id"]) == fc[0]:
                pz_state = "answered"
            elif int(P["id"]) == int(pz_pid or -1):
                pz_state = "catching"
            # (review 4) a count later than the first one after his Pursue: the Pursue is history, the row reads as any other
        if abs(float(g)) < 0.5:                               # a fresh short since put right in Marg: settled
            wo_o = [a for a in (open_by_item.get(norm(R["item"])) or []) if str(a.get("ref") or "").startswith("S969:wo:")]
            if wo_o:                                          # S969 re-look: a later count agrees with Marg while his write-off is not yet keyed
                wd_a = next((a for a in wo_o if not a.get("done_day")), None)   # S971: Withdraw the write-off Amir has not tapped done (second look S4)
                undone = wd_a is not None
                way.append(row(R, short_t="", box="way", acts=(["wd"] if undone else []), ref=(wd_a or {}).get("ref"), fig="Marg %s · shelf %s" % (st(R.get("marg_units"), pack), st(R.get("shelf_units"), pack)),
                               tags=[["red", "a later count agrees with Marg — not to be keyed"]],
                               path=[["ok", "Written off from this desk: %s, on Amir's card." % VJ._ask_line(wo_o[0])],
                                     ["now", ("A later count agrees with Marg and Amir has not keyed it yet: keying it now would put Marg below the shelf. "
                                              "Withdraw takes it off his card.") if undone else
                                      ("Amir tapped it done %s: if he keyed it, Marg's next report shows it and Marg goes below the shelf -- the next count "
                                       "brings it back to this desk." % VJ.dm(wo_o[0].get("done_day")))]]))
                continue
            if pz_state == "answered":                        # S969: the recount agrees with Marg -- the first count was a count error
                settled.append(row(R, short_t="", verdict="settled", path=_pz_path(pz, P, pack)
                                   + [["ok", "The recount agrees with Marg -- the first count was a count error; closed by itself, nothing to write off."]]))
                continue
            if P and P.get("gap") is not None and float(P["gap"]) <= -0.5:
                hits = [a for a in A if a.get("state") == "in_marg" and a.get("match") and VJ.name_match(set(a.get("forms") or []), R["item"])
                        and (a["match"].get("day") or "") >= P["at"][:10]]
                settled.append(row(R, short_t=st(-float(P["gap"]), pack), verdict="settled",
                                   path=[["ok", "%s's count of %s: %s short of Marg." % ("Darpan" if P["source"] == "darpan" else "The spot morning", dmy(P["at"]), st(-float(P["gap"]), pack))]]
                                   + ([["ok", "Written off in Marg: %s %s of %s -- closed by Marg's own report." % (h["kind"].title(), h["match"]["no"], VJ.dm(h["match"]["day"]))] for h in hits[:2]]
                                      or [["ok", "Marg agrees with the shelf today -- nothing left to do."]])))
            continue
        if float(g) > 0 or R.get("state") != "look":
            continue                                          # more on the shelf than in Marg: noted on the page below, never a loss
        short = -float(g)
        words = (P or {}).get("words") or ""
        base_txt = "%s's count of %s: %s counted, Marg %s at the time." % ("Darpan" if (P or {}).get("source") == "darpan" else "The spot morning",
                                                                        dmy(R.get("base_day")), st((P or {}).get("qty"), pack), st((P or {}).get("expected"), pack))
        r = row(R, short=int(round(short)), short_t=st(short, pack), words=words, awaits=((P or {}).get("status") == "awaits_sales"),
                fig="Marg %s · shelf %s · short %s" % (st(R.get("marg_units"), pack), st(R.get("shelf_units"), pack), st(short, pack)),
                pid=(P or {}).get("id"), pat=(P or {}).get("at"), qty=(P or {}).get("qty"), expected=(P or {}).get("expected"), acts=[])   # S969: the count the buttons act on
        if pz_state == "answered":
            r["path"] = _pz_path(pz, P, pack)                 # S969: both counts, the recount's judgment below
            r["tags"].append(["blu", "recounted"])
        else:
            r["path"].append(["ok", base_txt])
        if words:
            r["path"].append(["ok", "Judged: " + words])
        if r["awaits"]:
            r["tags"].append(["amb", "waits for today's sales"])
            r["path"].append(["now", "An evening count: judged when that day's sale report is in -- no buttons until then."])
        op = [a for a in (open_by_item.get(norm(R["item"])) or [])            # second look 2: the newest asking of it, whatever its figure
              if str(a.get("ref") or "").startswith("S969:wo:")             # S969 second look 1: his own write-off not yet in Marg, whatever its day
              or max([a.get("day") or "", a.get("reasked") or ""] + [h.get("asked") or "" for h in a.get("history") or []]) >= str(R.get("base_day") or "")]
        if not op and P and int(P["id"]) in WOP:              # S969 second look 4: written off, Marg's report has it, the record not yet
            inm = any(a.get("state") == "in_marg" and str(a.get("ref") or "").startswith("S969:wo:") and VJ.name_match(set(a.get("forms") or [norm(a["item"])]), R["item"]) for a in A)
            r["tags"].append(["grn", "written off — Marg's figure catches up"] if inm else ["amb", "written off — Marg not as asked"])
            r["path"].append(["now", "Written off from this desk; Marg's report shows it -- the figures agree once the stock of record is built again." if inm else
                                     "Written off from this desk; Marg's report does not show it as asked -- see box 3 for what Marg holds."])
            r["box"] = "way"
            way.append(r)
            continue
        if op or "not a new loss" in words:
            r["tags"].append(["blu", "already asked of Amir" if op else "an older loss Marg still holds"])
            r["path"].append(["now", ("On Amir's card: %s -- the next Stock Issue report closes it." % "; ".join(VJ._ask_line(a) for a in op[:2])) if op else
                              "The older loss is written off first; nothing new to ask."])
            r["box"] = "way"
            way.append(r)
            continue
        if pz_state in ("waiting", "catching"):               # S969: pursued -- no button until the recount is in the record
            r["tags"].append(["amb", "Pursue — on Darpan's list" if pz_state == "waiting" else "recounted — the record catches up"])
            r["path"].append(["now", ("You pursued it %s: a recount at the head of Darpan's next list -- the row comes back to you with both counts, or "
                                      "closes by itself if the recount agrees with Marg." % stamp(pz["at"])) if pz_state == "waiting" else
                              "Darpan has recounted it -- the row shows both counts once the stock of record is built again (within the hour)."])
            r["box"] = "short"
            box1.append(r)
            continue
        if "within the allowance" in words:
            a_u = _allowance(con, R["item"], pack, P) if P else None
            r["allowance_t"] = st(a_u, pack) if a_u is not None else ""
            r["tags"].append(["gry", "within the allowance" + ((" (%s)" % r["allowance_t"]) if r["allowance_t"] else "")])
            r["path"].append(["now", "Within your allowance -- the group button writes these off onto Amir's card, one Stock Issue voucher with the day's others."])
            r["box"] = "allow"
            r["wo_ok"] = (not r["awaits"]) and P is not None    # S969: the group button acts on these
            allow.append(r)
            continue
        if P is None or "never a loss" in words or not (r["awaits"] or "a loss" in words or "about a delivery" in words):
            r["tags"].append(["gry", "judgment not found" if P is None else "not judged a loss"])
            r["path"].append(["ok", ("The count this figure stands on was not found -- shown for your look; nothing to write off." if P is None else
                                     "The count's judgment did not call it a new loss -- shown for your look; nothing to write off.")])
            r["box"] = "noted"
            noted.append(r)                                    # second look 4: shown, never lost
            continue
        if "about a delivery" in words:
            r["tags"].append(["amb", "about a delivery -- count again"])
            r["path"].append(["now", "A delivery's worth short: a supply question, never a write-off -- Pursue puts a recount on Darpan's next list."])
            r["acts"] = [] if r["awaits"] else ["pu"]          # S969: count again first -- no Write off
        else:
            r["path"].append(["now", "Your call: Write off (a Stock Issue on Amir's card, with the day's others) or Pursue (a recount at the head of Darpan's next list)."])
            r["acts"] = [] if r["awaits"] else ["wo", "pu"]    # S969: nothing on an evening count still waiting for its sales
        r["box"] = "short"
        box1.append(r)
    box1.sort(key=lambda x: (-x["short"] // max(x["pack"], 1), x["item"]))
    # 2 · on its way to Marg: what is asked of Amir and not yet in Marg's report (the Expiry watch's night batch asks among them)
    groups = {}
    for a in A:
        if a.get("state") not in VJ.WAY_STATES:
            continue
        R = VJ.record_for(RR, set(a.get("forms") or {norm(a["item"])}))
        g = groups.setdefault(a["group"], dict(R=R, item=(R["item"] if R else a["item"]), asks=[]))
        g["asks"].append(a)
    seen_way = {norm(x["item"]) for x in way}
    for g in sorted(groups.values(), key=lambda g: (min(a["day"] or "" for a in g["asks"]), g["item"])):
        a0 = g["asks"][0]
        R = g["R"] or dict(item=g["item"], pack=a0.get("pack") or 1)
        V = VJ.whole_item(g["R"], g["item"], lo)
        path = []
        for h in a0.get("history") or []:
            fam = h["key"].split(":")[1] if h["key"].startswith("fix:") and ":" in h["key"][4:] else h["key"].split(":")[0]
            path.append(["ok", "Asked on Amir's card %s (%s)%s." % (VJ.dm(h["asked"]), fam, (", Amir tapped done %s" % VJ.dm(h["done"])) if h.get("done") else "")])
        if a0.get("reasked"):
            path.append(["ok", "Asked again %s after his done tap -- so it waits again (F-1706)." % VJ.dm(a0["reasked"])])
        path.append(["ok", "Whole item today: " + V["word"]])
        st_ = a0["state"]
        path.append(["now", {"waiting": "Waiting on Amir -- the next Stock Issue / Receive report closes it.",
                             "beyond": "Done after your newest Stock Issue / Receive report -- the next report decides.",
                             "gap": "Said done on a day no report covers -- a report of that period decides."}.get(st_, "")])
        if norm(g["item"]) in seen_way:
            for x in way:
                if norm(x["item"]) == norm(g["item"]):
                    x["path"] = x["path"][:-1] + path
            continue
        way.append(dict(row(R) if g["R"] else dict(item=g["item"], key="", pack=int(a0.get("pack") or 1), vlines=_vlines_for(VJ, con, g["item"], J), tags=[]),
                        fig=" + ".join(VJ._ask_line(a) for a in g["asks"]), src=VJ._src_word(a0), asked=VJ.dm(a0["day"]), path=path, verdict=V["v"],
                        tags=[["blu" if st_ == "waiting" else "amb", {"waiting": "waiting on Amir", "beyond": "after the newest report", "gap": "no report covers it"}.get(st_, st_)]]
                        + ([["gry", "batch fix"]] if a0["src"] == "batch" else []), box="way"))
    # S971: Amir's done taps a newer report lacks (the claim cards), in box 2; the ONE export line
    try:
        VI = _VI()
        for c in VI.claims_view(con):
            way.insert(0, dict(item=c["item"], key="", pack=1, vlines=_vlines_for(VJ, con, c["item"], J), fig=c["fig"], path=c["path"], tags=c["tags"],
                               acts=c["acts"], ref=c["id"], ask_ref=c.get("ask_ref"), box="way", claim=True))
        exportask = VI.export_need(con, J) if J.get("ok") else None
    except Exception:                                         # noqa: BLE001
        VI, exportask = None, None
    # 3 · old corrections, re-judged on the whole item
    old = []
    claimed = {x.get("ask_ref") for x in way if x.get("claim")}  # S971: an ask on a claim card is told in box 2 only (by the ask, review S8)
    J3 = dict(J, asks=[a for a in (J.get("asks") or []) if a.get("id") not in claimed]) if claimed else J
    for e in VJ.rejudge(con, J3, RR, lo):
        V = e["verdict"]
        R = e and (VJ.record_for(RR, {norm(e["item"])}))
        tagc = dict(settled="grn", count_first="blu", fresh_gap="red", held="gry", look="amb", unknown="gry", surplus="gry").get(V["v"], "gry")   # S975 (F-1738)
        path = [["ok", "Asked: %s (%s, %s)%s -- %s." % (x["ask"], x["src"], x["asked"], (", Amir said done " + x["done"]) if x["done"] else "", x["word"])] for x in e["asks"]]
        path += [["ok", "Marg's %s %s of %s: %s%s." % ("Issue" if m["kind"] == "ISSUE" else "Receive", m["no"], m["day"], m["word"], (" (" + m["ref"] + ")") if m["ref"] else "")] for m in e["marg_lines"]]
        path.append(["ok" if V["v"] in ("settled", "held", "surplus") else "now", "Whole item today: " + V["word"]])   # S975 (F-1738): a surplus waits for nobody
        where = ""
        if V["v"] == "fresh_gap":
            where = "box1" if any(norm(x["item"]) == norm(e["item"]) for x in box1) else ("way" if any(norm(x["item"]) == norm(e["item"]) for x in way) else "")
            path.append(["now", {"box1": "Today's gap is in box 1 above, for your Write off or Pursue.", "way": "Today's gap is already on Amir's card (box 2)."}.get(where, "Today's gap waits for your call.")])
        if e["batch_note"]:
            path.append(["ok", e["batch_note"][0].upper() + e["batch_note"][1:] + "."])
        r = row(R) if R else dict(item=e["item"], key="", pack=1, vlines=_vlines_for(VJ, con, e["item"], J), tags=[])
        r.update(verdict=V["v"], path=path, where=where, fig=("Marg %s · shelf %s" % (V["marg_t"], V["shelf_t"])) if V.get("marg_t") not in (None, "—") else "—",
                 tags=[[tagc, VJ.V_WORD[V["v"]]]] + ([["gry", "batch fix"]] if e["batch_note"] else []), box="old", count_btn=(V["v"] == "count_first"))
        if V["v"] == "settled":
            settled.append(dict(r, box="settled"))
        else:
            old.append(r)
    # 4 · vouchers nobody asked for -- history until his rule date (kit B starts the inquiry from it)
    rule = _setting(con, RULE_DATE_KEY)
    inq_open, inq_done, tally = ([], [], dict(month="", explained=0, reversed=0, closed=0, open=0))
    if VI is not None:                                        # review S1: open rows show whatever became of the rule date
        try:
            inq_open, inq_done, tally = VI.inquiry_view(con, rule or "")
        except Exception:                                     # noqa: BLE001
            pass
    inq_keys = {(x["kind"], x["no"], x["iso"]) for x in inq_open + inq_done}
    for x in inq_open + inq_done:
        x["vlines"] = []
        x["key"] = ""
        x["leds"] = []
        for it in sorted(set(x["items"])):
            R = VJ.record_for(RR, {norm(it)})
            x["leds"].append(dict(item=it, key=(R or {}).get("k20") or ""))
        x["voucher"] = next(([VJ._vline(y) for y in v["lines"]] for v in (J.get("vouchers") or []) if v["kind"] == x["kind"] and v["no"] == x["no"] and v["day"] == x["iso"]), [])
    moves = []
    for v in J.get("vouchers") or []:
        un = [ln for ln in v["lines"] if ln.get("state") == "unasked"]
        if not un:
            continue
        items = []
        for ln in un:
            R = VJ.record_for(RR, {norm(ln["item"])})
            V = VJ.whole_item(R, ln["item"], lo)
            items.append(dict(item=ln["item"], key=(R or {}).get("k20") or "", q=VJ.st(ln["units"], ln.get("per") or 1), batch=ln.get("batch") or "",
                              verdict=V["v"], word=V["word"], count_btn=(V["v"] == "count_first")))
        after = bool(rule) and v["day"] >= str(rule)
        if (v["kind"], v["no"], v["day"]) in inq_keys:
            continue                                          # S971: after the rule date its row is the inquiry's (below)
        moves.append(dict(kind=v["kind"], no=v["no"], day=VJ.dm(v["day"]), iso=v["day"], items=items, history=not after,
                          lines=[VJ._vline(x) for x in v["lines"]], waiting_sync=after))
    moves.sort(key=lambda m: (m["iso"], m["no"]), reverse=True)
    # S969 (F-1712): the old counts that differ from Marg -- their 'count again' reached no list. One tap puts each at the head of
    # Darpan's next list; nothing here is a write-off (an old count is never one). Items shown in boxes 3 and 4 keep their own Count button.
    shown = {norm(x["item"]) for x in old} | {norm(i["item"]) for m in moves for i in m["items"]} | {norm(i) for x in inq_open for i in x["items"]}   # S971: an inquiry row's items too
    onl = _open_asks(con)
    SWn = _SW()
    recount = []
    for k, R in sorted(RR.items()):
        if "old_base" not in str(R.get("marg_flag") or "") or R.get("state") != "look" or R.get("gap_units") is None or abs(float(R["gap_units"])) < 0.5:
            continue
        if norm(R["item"]) in shown or norm(R["item"]) in VJ.HELD:
            continue
        pack = int(R.get("pack") or 1) or 1
        on = onl.get(SWn.norm_name(R["item"]), "")
        recount.append(row(R, fig="Marg %s · shelf %s · %s" % (st(R.get("marg_units"), pack), st(R.get("shelf_units"), pack), st(R.get("gap_units"), pack, signed=True)),
                           box="recount", on_list=(dmy(on) if on else ""), acts=([] if on else ["nl"]),
                           tags=[["blu", "count first"]] + ([["amb", "on Darpan's list since %s" % dmy(on)]] if on else []),
                           path=[["ok", "The shelf figure is only the count of %s carried forward (Marg %s, shelf %s) -- an old count is never a write-off." % (
                                     dmy(R.get("base_day")), st(R.get("marg_units"), pack), st(R.get("shelf_units"), pack))],
                                 ["now", ("On Darpan's list since %s -- his count brings it to box 1 or settles it." % dmy(on)) if on else
                                  "Next list puts it at the head of Darpan's next morning list; his count brings it to box 1 or settles it."]]))
    recount.sort(key=lambda x: (bool(x["on_list"]), x["item"]))
    S = _SW().settings(con)
    try:
        import loss_piles as LP                               # noqa: PLC0415
        LS = LP.settings(con)
        apct, amin = LS["allowance_pct"], LS["allowance_min_strips"]
    except Exception:                                         # noqa: BLE001
        apct, amin = 1.0, 1
    settings = [dict(k="stock.allowance_pct", label="Allowance: share of the item's own sales since its last count", v="%g %%" % float(apct)),
                dict(k="stock.allowance_min_strips", label="Allowance: at least", v="%d strip(s) / piece(s)" % int(amin)),
                dict(k="stock.allowance_scale", label="Allowance scale", v=(_setting(con, "stock.allowance_scale") or "—") + " -- retired (S418): the judgment does not use it"),
                dict(k="evening_hour", label="A count at or after this hour waits for the day's sales", v="%s:00" % S.get("evening_hour", 17)),
                ]
    edit = []
    try:
        edit = VI.settings_view(con) if VI is not None else []
    except Exception:                                         # noqa: BLE001
        edit = []
    tot = dict(noted=len(noted), short=len(box1), allow=len(allow), way=len(way), old=len(old), moves=len(moves) + len(inq_open), moves_open=sum(1 for m in moves if not m["history"]) + len(inq_open),
               settled=len(settled), recount=len(recount), recount_open=sum(1 for x in recount if not x["on_list"]), inq_open=len(inq_open), inq_done=len(inq_done),
               inq_red=sum(1 for x in inq_open if x["tags"][0][0] == "red"), claims=sum(1 for x in way if x.get("claim")))
    return dict(ok=True, at=now_ist(), day=day, judge_ok=bool(J.get("ok")), box1=box1, allow=allow, way=way, old=old, moves=moves, settled=settled, noted=noted,
                recount=recount, settings=settings, edit=edit, rule_date=(dmy(rule) if rule else ""), totals=tot, fold=LEDGER_FOLD, version=VERSION, kit=KIT_S969,
                kit_b=KIT_S971, inquiry=inq_open, inquiry_done=inq_done, tally=tally, exportask=exportask)


@bp.route("/api/desk")
def r_desk():
    """S967: the one page's five boxes (desk), read only, at most once in CACHE_SECONDS (?fresh=1 rebuilds)."""
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    now = time.monotonic()
    if _DCACHE["v"] is not None and now - _DCACHE["at"] < CACHE_SECONDS and str(request.args.get("fresh") or "") not in ("1", "yes"):
        return jsonify(dict(_DCACHE["v"], can_write=_can_write()))   # S969: the buttons only for the owner
    con = _db()
    if not _require("checker")[1]:                            # S971: the owner's read keeps Amir's cards up to date first (review S5: the owner only,
        try:                                                  # at most once in 5 minutes; a viewer's or Darpan's read never writes)
            _VI().sync_maybe(con)
        except Exception as e:                                # noqa: BLE001
            try:
                con.rollback()
            except Exception:                                 # noqa: BLE001
                pass
            print("stock_check: S971 sync stopped: %s" % str(e)[:200], file=sys.stderr)
    try:
        v = desk(con)
    except Exception as e:                                    # noqa: BLE001
        return jsonify(ok=False, reason="The boxes could not be built: %s" % type(e).__name__), 200
    if v.get("ok"):
        _DCACHE["v"], _DCACHE["at"] = v, now
    return jsonify(dict(v, can_write=_can_write()))


@bp.route("/api/desk/act", methods=["POST"])
def r_desk_act():
    """S969: the desk's writes, the owner only -- {act: writeoff | pursue | allow | nextlist, item, items}. The desk is built afresh first;
    a button acts only on a row the desk offers it on (a double tap, or a row moved meanwhile, writes nothing)."""
    u, err = _require("checker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    act = str(b.get("act") or "").strip().lower()
    item = re.sub(r"\s+", " ", str(b.get("item") or "")).strip()[:80]
    items = [re.sub(r"\s+", " ", str(x or "")).strip()[:80] for x in (b.get("items") or []) if str(x or "").strip()][:80]
    S971_ACTS = ("withdraw", "back", "cclose", "reverse", "close", "dumpok", "setting")
    if act not in ("writeoff", "pursue", "allow", "nextlist") + S971_ACTS:
        return jsonify(ok=False, message="Unknown button."), 400
    who = (u or {}).get("user") or (u or {}).get("username") or ""
    con = _db()
    if act in S971_ACTS:                                      # S971: Amir by himself -- each tap checks its own row's state (no stale write)
        try:
            VI = _VI()
            VI.ensure(con)
            if act == "setting":
                ok_, msg = VI.set_setting(con, str(b.get("key") or ""), b.get("value"), who)
            elif act == "withdraw":
                K = desk(con)
                hit = [r for r in K.get("way") or [] if r["item"] == item and "wd" in (r.get("acts") or []) and (not b.get("ref") or r.get("ref") == b.get("ref"))]
                if not hit:
                    return jsonify(ok=False, message="That row no longer offers Withdraw -- the page reads again."), 409
                ok_, msg = VI.withdraw_writeoff(con, item, who, hit[0].get("ref"))
            else:
                ok_, msg = VI.act(con, act, b.get("ref"), who, b.get("note") or "")
        except Exception as e:                                # noqa: BLE001
            try:
                con.rollback()
            except Exception:                                 # noqa: BLE001
                pass
            return jsonify(ok=False, message="Not written: %s." % type(e).__name__), 500
        _DCACHE["v"], _VCACHE["v"], _CACHE["rec"] = None, None, None
        return jsonify(ok=ok_, message=msg), (200 if ok_ else 409)
    try:
        K = desk(con)
    except Exception as e:                                    # noqa: BLE001
        return jsonify(ok=False, message="The desk could not be built just now (%s) -- nothing written." % type(e).__name__), 200
    if not K.get("ok"):
        return jsonify(ok=False, message=K.get("reason") or "The desk is not ready -- nothing written."), 409
    if not K.get("judge_ok"):                                 # review 3: without the judge a row already asked of Amir would look new
        return jsonify(ok=False, message="Marg's stock vouchers could not be judged just now -- nothing written. Try again in a minute."), 409
    if act == "writeoff":
        rows = [r for r in K["box1"] if r["item"] == item and "wo" in (r.get("acts") or [])]
    elif act == "pursue":
        rows = [r for r in K["box1"] if r["item"] == item and "pu" in (r.get("acts") or [])]
    elif act == "allow":
        rows = [r for r in K["allow"] if r.get("wo_ok") and (r["item"] in items)]
    else:
        rows = [r for r in K["recount"] if "nl" in (r.get("acts") or []) and ((r["item"] == item) if item else (r["item"] in items))]
    if not rows:
        return jsonify(ok=False, message="That row no longer offers this button -- the page reads again."), 409
    try:
        if act in ("writeoff", "allow"):
            made, skipped = _write_off(con, rows, who, "allow" if act == "allow" else "short")
            msg = ("On Amir's card: %s -- one Stock Issue voucher with the day's others." % ", ".join(made)) if made else "Already on Amir's card -- nothing new written."
            if made and skipped:
                msg += " Already there: %s." % ", ".join(skipped)
            ok_ = bool(made)
        elif act == "pursue":
            ok_, m = _pursue(con, rows[0], who)
            msg = ("Pursued: %s" % m) if ok_ else m
        else:
            put = _next_list(con, rows, who)
            ok_ = bool(put)
            msg = ("On Darpan's next list: %d item%s." % (len(put), "" if len(put) == 1 else "s")) if put else "Nothing put on the list."
    except Exception as e:                                    # noqa: BLE001
        try:
            con.rollback()
        except Exception:                                     # noqa: BLE001
            pass
        return jsonify(ok=False, message="Not written: %s." % type(e).__name__), 500
    _DCACHE["v"], _VCACHE["v"], _CACHE["rec"] = None, None, None
    return jsonify(ok=ok_, message=msg), 200


@bp.route("/api/find")
def r_find():
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    q = str(request.args.get("q") or "").strip()[:60]
    SW = _SW()
    sp = SW.Spine()
    return jsonify(ok=True, items=[x["name"] for x in (sp.search(q, 12) if (sp.ok and len(q) >= 2) else [])])


@bp.route("/api/healthz")
def r_healthz():
    return jsonify(ok=True, kit=KIT, version=VERSION, page=os.path.exists(PAGE), desk=True, writes=True, kit_desk=KIT_S969, kit_b=KIT_S971, losses=True)


# ------------------------------------------------------------------ S971: THE LOSS REGISTER (his word 17:17 IST 27-Nov) -- his only, read only
LOSS_PAGE = os.path.join(HERE, "stock_losses.html")


@bp.route("/api/losses")
def r_losses():
    u, err = _require("checker")
    if err:
        return err
    try:
        return jsonify(dict(ok=True, at=now_ist(), **_VI().losses(_db())))
    except Exception as e:                                    # noqa: BLE001
        return jsonify(ok=False, reason="The loss register could not be read: %s" % type(e).__name__), 200


@bp.route("/losses")
def r_losses_page():
    u, err = _require("checker")
    if err:
        return err
    try:
        with io.open(LOSS_PAGE, "r", encoding="utf-8") as fh:
            t = fh.read()
    except OSError:
        return jsonify(ok=False, error="template_missing", message="stock_losses.html is not beside stock_check.py"), 503
    return t, 200, {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store"}


# ---- S975 (28-Nov-2026, Sanjeevni session 542, kit S975_STOCKCHECK_V10; D1106 -- mock-up v10, his 'OK' 11:52 IST) --------------------
#  The one page in three bands: 1 his write-offs waiting for Amir (the loss register's open lines) . 2 today's counts, one plain verdict
#  each (and any earlier count still waiting for his call) . 3 waiting on others (the existing boxes, folded). desk() keeps every box as
#  before -- the desk's writes and the earlier walks read them -- and ADDS band1, band2, earlier, week, way3 and v10 totals. A row is shown
#  once: an item of band 1 leaves way3 (box 2 as drawn) unless it waits on another correction too. F-1738: a fresh surplus is told
#  'more than Marg -- noted, never a loss' in box 3 (voucher_judge's 'surplus'). CCM (the whole-unit list) is told in its bottles.
KIT_S975 = "S975_STOCKCHECK_V10"
VERSION = "1.9"                                              # v1.9 S975: the three bands (band1 . band2 . earlier . week . way3)
WEEK_DAYS = 7
_desk_before_s975 = desk


def _s975_dm(iso):
    s = str(iso or "")[:10]
    return "%s-%s" % (s[8:10], s[5:7]) if len(s) == 10 else s


def _s975_whole(con, item):
    """The whole-unit word of an item ('bottle' for CCM, the desk's stock.whole_unit_items), or None."""
    try:
        import loss_piles as LP                               # noqa: PLC0415 -- loads the whole-unit map into qty_words
        LP.settings(con)
        import qty_words as QW                                # noqa: PLC0415
        return QW.whole_unit_of(item)
    except Exception:                                         # noqa: BLE001
        return None


def _s975_q(units, pack, whole=None, signed=False):
    """A count's figure in the record's own unit: strips:tabs; for an item Marg counts whole ('CCM = bottle') whole packs read as that
    word (the count screen stores a pack of the record's size for each one)."""
    if units is None:
        return "—"
    u = float(units)
    if whole and pack > 1 and abs(u - round(u / pack) * pack) < 0.5:
        n = int(round(u / pack))
        w = "%d %s%s" % (abs(n), whole, "" if abs(n) == 1 else "s")
        return (("−" if n < 0 else ("+" if n > 0 else "")) + w) if signed else w
    return st(u, pack, signed=signed)


def _s975_band1(con, VJ, VI, J, RR, day):
    """Band 1: every write-off of his that Marg's report does not hold yet -- the loss register's open lines (not withdrawn)."""
    if not _has(con, "stock_desk_action") or VI is None:
        return [], None, {}
    jst = {}
    for a in J.get("asks") or []:
        for k in (a.get("jobs") or [a.get("ref")]):
            if str(k or "").startswith("S969:wo:"):
                jst[k] = a
    L = VI.losses(con, J)
    lines = {ln["id"]: ln for m in L.get("months") or [] for ln in m["lines"]}
    month = next((m for m in L.get("months") or [] if m["month"] == str(day)[:7]), None)
    foot = dict(label=month["label"], n=month["n"], cost_t=month["cost_t"], mrp_t=month["mrp_t"]) if month else None
    out, WS = [], {}                                          # WS: the counts he wrote off -> 'above' (band 1) . 'withdrawn' . 'in Marg' . 'closed'
    d0 = dt.date.fromisoformat(day)
    for (i, item, pack, units, key, dday, at, by, batch, pat, pid) in con.execute(
            "SELECT id, item, pack, units, job_key, day, at, by, batch, point_at, point_id FROM stock_desk_action WHERE kind='writeoff' ORDER BY at, id").fetchall():
        ln = lines.get(i)
        pid_ = int(pid) if pid else None
        def mark(w):
            if pid_ is not None:
                WS[pid_] = w
        if ln is None:
            mark("closed"); continue
        if ln.get("withdrawn"):
            mark("withdrawn"); continue
        a = jst.get(key)
        if a and a.get("state") == "in_marg" and a.get("match"):
            mark("in Marg"); continue                         # in Marg: closed, the loss register keeps it
        if a and a.get("state") not in VJ.WAY_STATES + ("not_in_marg",):
            mark("closed"); continue                          # (cold review 4) fixed otherwise / in Marg not as asked: never twice
        jr = con.execute("SELECT done_at, done_how FROM amir_job WHERE key=?", (key,)).fetchone() if key else None
        if jr and jr[1] == "withdrawn":
            mark("withdrawn"); continue
        mark("above")
        done = bool(jr and jr[0])
        try:
            days = (d0 - dt.date.fromisoformat(str(dday)[:10])).days
        except ValueError:
            days = 0
        stt = (a or {}).get("state") or ""
        card = "STOCK ISSUE · %s" % _s975_dm(dday)
        if done:
            cs = "Kar diya %s — %s" % (_s975_dm(jr[0]), "Marg's newer report lacks it" if stt == "not_in_marg" else
                                       ("a report of that period decides" if stt == "gap" else "the next report decides"))
            tags = [["red" if stt == "not_in_marg" else "amb", cs]]
        else:
            cs = ("today" if days <= 0 else "%d day%s" % (days, "" if days == 1 else "s")) + " — not done"
            tags = [["red" if days >= 2 else "blu", "on Amir's card, " + cs]]
        R = VJ.record_for(RR, {norm(item)})
        path = [["ok", "The count: %s." % ln["count"]] if ln.get("count") not in (None, "", "—") else ["ok", "The count this write-off acts on is not named."],
                ["ok", "Your tap %s: Write off %s (%s)%s." % (stamp(at), ln["q"], ln["group"], (" by " + str(by).title()) if by else "")],
                ["ok" if done else "now", "On Amir's card: %s — %s %s%s; %s." % (card, item, ln["q"], (" · batch " + batch) if batch else "", cs)],
                ["now", "It closes by itself when Marg's Stock Issue report shows the voucher (the voucher judge). The loss register keeps "
                        "it either way, its value fixed on the day of your tap."]]
        out.append(dict(item=item, key=(R or {}).get("k20") or "", pack=int(pack or 1), q=ln["q"], booked=_s975_dm(dday), card=card, card_state=cs,
                        done=done, track=[["ok", "Booked " + _s975_dm(dday)], ["ok" if done else "now", "Amir keys it" + ((" · Kar diya " + _s975_dm(jr[0])) if done else "")],
                                          ["now" if done else "wait", "In Marg"]],
                        cost_t=ln.get("cost_t") or "", mrp_t=ln.get("mrp_t") or "", tags=tags, path=path, acts=[], ref=None, box="band1",
                        job=key or "", pat=str(pat or ""), day=str(dday or "")[:10], at=str(at or "").replace(" ", "T")[:19],
                        fig="written off %s · booked %s · %s" % (ln["q"], _s975_dm(dday), (ln.get("cost_t") or "")),
                        vlines=_vlines_for(VJ, con, item, J)))
    return out, foot, WS


def _s975_point_rows(con, d1, d2):
    """stock_point rows of the spot mornings and Darpan with d1 <= day <= d2, newest first; a count replaced by a later one is left out."""
    cols = {r[1] for r in con.execute("PRAGMA table_info(stock_point)")}
    jw = "judge_words" if "judge_words" in cols else "NULL"
    return [dict(id=r[0], item=r[1], at=str(r[2]), qty=r[3], expected=r[4], gap=r[5], source=r[6], status=str(r[7] or ""), words=str(r[8] or ""),
                 by=str(r[9] or "")) for r in con.execute(
        "SELECT id, item, at, qty_units, expected_units, gap_units, source, status, %s, by FROM stock_point WHERE substr(at,1,10)>=? AND "
        "substr(at,1,10)<=? AND source IN ('spot','darpan') AND COALESCE(status,'') NOT IN ('superseded') ORDER BY at DESC, id DESC" % jw, (d1, d2))]


def _s975_count_row(con, VJ, J, RR, P, rowmap, WOP, b1items):
    """One count, one plain verdict: dict(item, key, fig, tags, acts, path, verdict, surplus, day, time, by)."""
    R = VJ.record_for(RR, {norm(P["item"])})
    pack = int((R or {}).get("pack") or 1) or 1
    whole = _s975_whole(con, P["item"]) if pack > 1 else None
    g = P["gap"]
    unclear = bool(whole and P["qty"] is not None and abs(float(P["qty"]) - round(float(P["qty"]) / pack) * pack) >= 0.5)   # second look 4
    exp_t = (("%d %s%s" % (int(round(float(P["expected"]))), whole, "" if int(round(float(P["expected"]))) == 1 else "s")) if whole and P["expected"] is not None
             else st(P["expected"], pack))
    if unclear:
        gap_t = "not compared"
    elif whole and P["qty"] is not None and P["expected"] is not None and abs(float(P["qty"]) - round(float(P["qty"]) / pack) * pack) < 0.5:
        g = round(float(P["qty"]) / pack) - float(P["expected"])   # CCM: the screen's packs are bottles, Marg's figure already is
        gap_t = ("+" if g > 0 else ("−" if g < 0 else "")) + "%d %s%s" % (abs(int(round(g))), whole, "" if abs(int(round(g))) == 1 else "s") if abs(g) >= 0.5 else "0"
    else:
        gap_t = st(g, pack, signed=True) if g is not None else "—"
    r = rowmap.get(int(P["id"]))
    src = "Darpan" if P["source"] == "darpan" else "The spot morning"
    base = ["ok", "%s's count at %s: %s counted, Marg %s at the time%s." % (src, stamp(P["at"]), _s975_q(P["qty"], pack, whole), exp_t,
                                                                          (" -- Marg counts %s by the %s" % (P["item"], whole)) if whole else "")]
    d = dict(item=P["item"], key=(R or {}).get("k20") or "", pack=pack, day=P["at"][:10], time=P["at"][11:16], by=(P["by"] or "").title(), src=src.replace("The spot", "Spot"),
             fig="counted %s · Marg %s · %s" % (_s975_q(P["qty"], pack, whole), exp_t, gap_t), tags=[], acts=[], path=[base], surplus=False,
             verdict="", vlines=_vlines_for(VJ, con, P["item"], J), pid=int(P["id"]), box="band2")
    if P["words"]:
        d["path"].append(["ok", "Judged: " + P["words"]])
    box = (r or {}).get("box") or ""
    b1a = [x.get("at") or (x.get("day", "") + "T23:59:59") for x in b1items.get(norm(P["item"])) or []]
    w_ = (WOP.get(int(P["id"]), "above") if isinstance(WOP, dict) else "above") if int(P["id"]) in WOP else None
    if w_ == "above":
        d.update(verdict="wo", tags=[["grn", "written off by you — above"]])
        d["path"].append(["now", "Written off from this desk: band 1 above follows it to Marg."])
    elif w_:
        d.update(verdict="wo_" + w_.split()[0].lower(), tags=[["gry", "your write-off of it was withdrawn"] if w_ == "withdrawn" else
                                                                ["grn", "written off by you — in Marg" if w_ == "in Marg" else "written off by you — closed"]])
    elif P["status"] in ("recounted", "recount"):
        d.update(verdict="recounted", tags=[["gry", "recounted — see the next count"] if P["status"] == "recounted" else ["amb", "held for a recount"]])
    elif unclear:
        d.update(verdict="unit", tags=[["amb", "stored %s — its unit is unclear (Marg counts %s by the %s); see the item ledger" % (st(P["qty"], pack), P["item"], whole)]])
    elif not r and b1a and g is not None and float(g) <= -0.5 and P["at"].replace(" ", "T")[:19] < max(b1a):
        d.update(verdict="before_wo", tags=[["gry", "before your write-off of %s — band 1 above" % _s975_dm(max(b1a))]])
        d["path"].append(["ok", "A count before your write-off of %s; band 1 above follows that write-off to Marg." % _s975_dm(max(b1a))])
    elif whole and not r and g is not None and float(g) <= -0.5:
        d.update(verdict="unit_loss", tags=[["amb", "%s short — the stock record cannot judge this item yet (its pack); see the item ledger" % gap_t.lstrip("−")]])
        d["path"].append(["now", "Marg counts %s by the %s, the stock record by a pack of %d: no Write off is offered until the record's pack is put right." % (P["item"], whole, pack)])
    elif r and box == "allow":
        d.update(verdict="allow", tags=list(r.get("tags") or []) or [["amb", "within your allowance"]], wo_ok=r.get("wo_ok"))
        d["tags"] = [["amb", t[1]] if t[0] == "gry" else t for t in d["tags"]]
        d["path"] = list(r.get("path") or d["path"])
    elif r and box == "short":
        d.update(verdict="loss", acts=list(r.get("acts") or []), short_t=r.get("short_t") or "", tags=list(r.get("tags") or []))
        if d["acts"]:
            d["tags"].insert(0, ["red", "a loss since the last count — your call"])
        d["path"] = list(r.get("path") or d["path"])
    elif r and box == "way":
        d.update(verdict="way", tags=list(r.get("tags") or []), acts=list(r.get("acts") or []), ref=r.get("ref"))
        d["path"] = list(r.get("path") or d["path"])
    elif r and box == "noted":
        d.update(verdict="noted", tags=list(r.get("tags") or []))
        d["path"] = list(r.get("path") or d["path"])
    elif P["status"] == "awaits_sales":
        d.update(verdict="awaits", tags=[["amb", "waits for the day's sales"]])
        d["path"].append(["now", "An evening count: judged when that day's sale report is in."])
    elif g is None:
        d.update(verdict="none", tags=[["gry", "not judged yet"]])
    elif abs(float(g)) < 0.5:
        d.update(verdict="agree", tags=[["grn", "agrees with Marg"]])
    elif float(g) > 0:
        d.update(verdict="surplus", surplus=True, tags=[["gry", "more than Marg — never a loss"]])
        d["path"].append(["ok", "More on the shelf than in Marg: noted, never a loss; nothing waits for your call."])
    elif "within the allowance" in P["words"]:
        d.update(verdict="allow", tags=[["amb", "within your allowance"]])
    else:
        d.update(verdict="short", tags=[["gry", "short — its row is in the boxes below"]])
        d["path"].append(["now", "The stock of record stands on a later figure now; the boxes below tell what is left of it."])
    return d


def _s975_bands(con, v, day):
    import voucher_judge as VJ                                # noqa: PLC0415
    RR = VJ.record_rows(con)
    try:
        J = VJ.judge(con, day)
    except Exception:                                         # noqa: BLE001
        J = dict(ok=False, asks=[], lines=[], vouchers=[])
    try:
        VI = _VI()
    except Exception:                                         # noqa: BLE001
        VI = None
    band1, foot, WS = _s975_band1(con, VJ, VI, J, RR, day)
    b1 = {}
    for x in band1:                                           # (cold review 5) every open write-off of an item, oldest first
        b1.setdefault(norm(x["item"]), []).append(x)
    # a row is shown once: box 2's rows of a band-1 item leave way3 -- unless the item waits on another correction too;
    # a Withdraw (a later count agrees with Marg, not to be keyed) moves onto the band-1 row
    other = set()
    for a in J.get("asks") or []:
        if a.get("state") not in VJ.WAY_STATES + ("not_in_marg",):
            continue
        if str(a.get("ref") or "").startswith("S969:wo:") or any(str(k or "").startswith("S969:wo:") for k in (a.get("jobs") or [])):
            continue
        for k in b1:
            if VJ.name_match(set(a.get("forms") or {norm(a["item"])}), b1[k][0]["item"]):
                other.add(k)
    way3 = []
    for r in v.get("way") or []:
        k = norm(r.get("item") or "")
        if r.get("claim") or k not in b1:
            way3.append(r)
            continue
        x = next((y for y in b1[k] if y["job"] and y["job"] == r.get("ref")), b1[k][-1])
        moved = False
        if "wd" in (r.get("acts") or []) and not x["acts"]:
            x.update(acts=["wd"], ref=r.get("ref")); moved = True
        for t in r.get("tags") or []:
            if t not in x["tags"] and "already asked" not in t[1]:
                x["tags"].append(t)
        for p in r.get("path") or []:
            if p[0] == "now" and p not in x["path"] and "On Amir's card" not in p[1]:
                x["path"].insert(len(x["path"]) - 1, p)
        if k in other:
            way3.append(dict(r, tags=list(r.get("tags") or []) + [["gry", "your write-off: band 1 above"]],
                             acts=[q for q in (r.get("acts") or []) if not (moved and q == "wd")]))   # second look 5: Withdraw once
    for r in v.get("old") or []:                              # box 3: today's gap of an item he wrote off is told as band 1's, never red
        k = norm(r.get("item") or "")
        Rb = VJ.record_for(RR, {k})                           # (cold review 3) only when today's gap stands on the very count he wrote off
        if k in b1 and r.get("verdict") == "fresh_gap" and Rb and any(y["pat"] and y["pat"][:16].replace(" ", "T") == str(Rb.get("base_at") or "")[:16].replace(" ", "T") for y in b1[k]):
            r["tags"] = [["blu", "your write-off — band 1 above"]] + list(r.get("tags") or [])[1:]
            r["path"] = [(["ok", "Today's gap is your write-off -- band 1 above follows it to Marg."] if "Today's gap" in p[1] else p) for p in r.get("path") or []]
    rowmap = {}
    for name in ("box1", "allow", "way", "noted"):
        for r in v.get(name) or []:
            if r.get("pid") is not None:
                rowmap.setdefault(int(r["pid"]), r)
    WOP = dict(WS)                                           # second look 1: what became of each count he wrote off
    for p_ in _wo_points(con):
        WOP.setdefault(int(p_), "closed")
    today_rows = [_s975_count_row(con, VJ, J, RR, P, rowmap, WOP, b1) for P in _s975_point_rows(con, day, day)]
    shown = {x["pid"] for x in today_rows}
    # (cold review 1) every box-1 / allowance row not drawn as today's count stays visible here -- with or without its buttons
    # (a Pursue waiting on Darpan, an evening count waiting for its sales), whatever the count's age; it never repeats in the week fold
    earlier = [r for r in (v.get("box1") or []) + (v.get("allow") or []) if r.get("pid") is None or int(r["pid"]) not in shown]
    held = {int(r["pid"]) for r in earlier if r.get("pid") is not None}
    d7 = (dt.date.fromisoformat(day) - dt.timedelta(days=WEEK_DAYS)).isoformat()
    d1 = (dt.date.fromisoformat(day) - dt.timedelta(days=1)).isoformat()
    week = [_s975_count_row(con, VJ, J, RR, P, rowmap, WOP, b1) for P in _s975_point_rows(con, d7, d1) if int(P["id"]) not in held]
    counters = sorted({x["by"] or x["src"] for x in today_rows})
    aw = [r["item"] for r in (v.get("allow") or []) if r.get("wo_ok")]
    tot = dict(band1=len(band1), today=len(today_rows), way3=len(way3), recount=sum(1 for r in v.get("recount") or [] if not r.get("on_list")),
               earlier=len(earlier), week=len(week), allow_wo=len(aw), b1_done=sum(1 for x in band1 if x["done"]))
    return dict(v10=True, kit_v10=KIT_S975, band1=band1, band1_foot=foot, band2=today_rows, earlier=earlier, week=week, way3=way3,
                counters=counters, day_word=day_word(day), allow_items=aw, v10_totals=tot, version=VERSION)


def desk(con, day=None):                                      # noqa: F811 -- S975: the boxes as before, plus the three bands
    _s975_whole(con, "")                                     # the whole-unit map loaded before the judge reads it (second look 3)
    v = _desk_before_s975(con, day)
    if not v.get("ok"):
        return v
    try:
        v.update(_s975_bands(con, v, v.get("day") or day or today().isoformat()))
    except Exception as e:                                    # noqa: BLE001
        v.update(v10=False, v10_reason="The new layout could not be built just now (%s) -- the boxes as before." % type(e).__name__)
        print("stock_check: S975 bands stopped: %s" % str(e)[:200], file=sys.stderr)
    return v
# ---- S975 end ---------------------------------------------------------------------------------------------------------------------------
