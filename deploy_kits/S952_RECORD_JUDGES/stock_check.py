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
import datetime as dt
import html as _html
import io
import os
import re
import sqlite3
import sys
import time

from flask import Blueprint, jsonify, redirect, request

VERSION = "1.4"                                             # v1.3 S934: Count now / Next list, withdraw, a count placed to its bill; v1.2 S933: every figure from stock_record (the stock of record); v1.1: the cold review's points
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
        nd = SW.next_roster_day(S)
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
    return jsonify(ok=True, kit=KIT, version=VERSION, page=os.path.exists(PAGE))
