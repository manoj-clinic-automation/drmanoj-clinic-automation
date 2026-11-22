#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
#  hub_panels.py  ·  v1.0  ·  kit S927_HUB_NEEDS_YOU_INLINE  ·  Session 502 (Sanjeevni)  ·  D1039 (his words 09:39 and 12:08, 22-Nov-2026)
#
#  THE HUB'S NEEDS-YOU, WORKABLE INLINE.  Every line of the owner's Needs-you can open under itself with the thing it is about and its own
#  buttons, so an audit never leaves the page (his words: "counted as arrived, not in Marg — should open inline the scan and purchase
#  lines etc, so that full audit can be done without leaving the page; and do this wherever applicable").
#
#    decorate(con, r)   -- the lines sanjeevni_approvals built, each given its panel kind + ref + since/age where the source knows them;
#                          lines he marked Seen (hub_seen) left out for their time; the retired 'Orthotic shortages' line left out while the
#                          purchase-flow line stands (every item is a shortage row there, S926).
#    GET  /finance/sanjeevni/api/needs-you/panel?kind=K&ref=R   -- the HTML fragment of one line's panel (checker and above):
#         porders  -- the S926 section (order_flow.team_table_s926) with its own doors
#         arrived  -- one order line counted as arrived and not in Marg: the order, the scan (thumbnail, full size, its read lines), Marg's
#                     purchase lines from that dealer since the arrival, the Marg stock; doors: Ask Amir to enter it · It is this Marg line
#                     · Never came
#         tapped   -- goods tapped as arrived with no bill: the order's lines and who tapped (read only; the arrow opens the page)
#         voucher  -- a count voucher Marg never moved: the words, Amir's job state; door: Ask Amir again
#         expiry   -- the expiry watch's current list (read only)
#         seen     -- an information line: door Seen (30 days)
#    POST /finance/sanjeevni/api/needs-you/act  {do, ...}        -- amir_ask · marg_line · never_came · voucher_again · seen
#  Writes: hub_seen (new), amir_job (a tap job, its own shape), purchase_order_line (billed_* as porders.detect_supplies writes them, or
#  supplied/short for 'never came'), med_name (a Marg partner the owner confirmed by picking the line). Never Marg, purchase_line, stock.
#  No patient data anywhere here. Fail-soft: a panel that cannot be built says so in one line; decorate() returns the lines unchanged on any fault.
# =============================================================================
import datetime as dt
import hashlib
import html as _html
import json
import re
import sqlite3
import sys

from flask import Blueprint, jsonify, request

VERSION = "1.0"
KIT = "S927_HUB_NEEDS_YOU_INLINE"
SEEN_DAYS = 30
bp = Blueprint("hub_panels_s927", __name__)
_db = _require = None
_unit = "medical"
DDL = ("CREATE TABLE IF NOT EXISTS hub_seen (id INTEGER PRIMARY KEY, key TEXT NOT NULL, text TEXT, until TEXT NOT NULL, by TEXT NOT NULL, at TEXT NOT NULL)",
       "CREATE INDEX IF NOT EXISTS hub_seen_key ON hub_seen (key, until)")


def init(app, db_getter, require_fn, unit="medical"):
    global _db, _require, _unit
    _db, _require, _unit = db_getter, require_fn, unit
    app.register_blueprint(bp)
    return bp


def esc(s):
    return _html.escape(str(s if s is not None else ""), quote=True)


def now_iso():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def ensure(con):
    for d in DDL:
        try:
            con.execute(d)
        except sqlite3.Error:
            pass


def _key(text):
    """The line's identity for Seen: its words without the moving figures (days ago, dates, counts), so a line marked Seen stays seen."""
    t = re.sub(r"\([^)]*\)", "", str(text or ""))              # '(22 days ago)', '(20 days)'
    t = re.sub(r"\d[\d,.:/-]*", "#", t)                           # every figure and date -> #
    return hashlib.md5(re.sub(r"\s+", " ", t).strip().lower().encode("utf-8")).hexdigest()[:16]


def ddmm(iso):
    s = str(iso or "")[:10]
    return "%s-%s" % (s[8:10], s[5:7]) if len(s) == 10 else s


def _age(since):
    try:
        return (dt.date.today() - dt.date.fromisoformat(str(since)[:10])).days
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------ the lines, decorated
def seen_keys(con):
    ensure(con)
    today = dt.date.today().isoformat()
    try:
        return {r[0] for r in con.execute("SELECT key FROM hub_seen WHERE until>=?", (today,))}
    except sqlite3.Error:
        return set()


def decorate(con, r):
    """The Needs-you answer with each line's panel (kind, ref), since and age_days; Seen lines out; the Orthotic line out beside S926's."""
    lines = list(r.get("lines") or [])
    seen = seen_keys(con)
    has_flow = any(str(l.get("text") or "").startswith("Purchase orders:") for l in lines)
    out = []
    for l in lines:
        t = str(l.get("text") or "")
        if _key(t) in seen:
            continue
        if has_flow and t.startswith("Orthotic shortages:"):
            continue                                              # retired: every orthotic shortage is a row of the purchase flow (S926)
        l = dict(l)
        if not l.get("panel"):
            tg = str(l.get("target") or "")
            if t.startswith("Purchase orders:"):
                l["panel"], l["ref"] = "porders", ""
            elif t.startswith("Goods tapped as arrived on "):
                m = re.match(r"Goods tapped as arrived on (\d\d-\d\d) from (.+?): no bill", t)
                l["panel"], l["ref"] = "tapped", ("%s|%s" % (m.group(2), m.group(1))) if m else ""
                if m:
                    l["since"] = _since_from_ddmm(m.group(1))
            elif t.startswith("Voucher ") and " the voucher said " in t:
                m = re.match(r"Voucher .*?: (.+?) — ", t) or re.match(r"Voucher .*?: (.+?) -- ", t)
                l["panel"], l["ref"] = "voucher", (m.group(1) if m else "")
            elif tg == "expiry":
                l["panel"], l["ref"] = "expiry", ""
            elif l.get("cls") == "info":
                l["panel"], l["ref"] = "seen", ""
        if l.get("since") and l.get("age_days") is None:
            l["age_days"] = _age(l["since"])
        l["key"] = _key(t)
        out.append(l)
    r = dict(r)
    r["lines"] = out
    r["count"] = len(out)
    return r


def _since_from_ddmm(dm):
    try:
        d, m = int(dm[:2]), int(dm[3:5])
        y = dt.date.today().year
        cand = dt.date(y, m, d)
        if cand > dt.date.today():
            cand = dt.date(y - 1, m, d)
        return cand.isoformat()
    except (TypeError, ValueError):
        return ""


# ------------------------------------------------------------------ the panels
def _pa():
    import purchase_app                                           # noqa: PLC0415
    return purchase_app


def _norm(s):
    try:
        return _pa().norm(s)
    except Exception:                                             # noqa: BLE001
        return re.sub(r"\s+", " ", str(s or "").upper()).strip()


def _btn(label, body, cls=""):
    return '<button class="%s" onclick=\'hpTwo(this,%s)\'>%s</button>' % (cls, esc(json.dumps(body)), esc(label))


PCSS = """<style>
.hp{font:14px/1.5 "Segoe UI",system-ui,sans-serif;color:#16202a}.hp .box{border:1px solid #d9dee4;border-radius:8px;background:#fff;padding:8px 10px;margin-top:6px}
.hp table{border-collapse:collapse;width:100%;font-size:13.5px;margin:4px 0}.hp th{text-align:left;color:#5b6773;font-weight:600;font-size:12px;padding:3px 6px;border-bottom:1px solid #e3e7eb}
.hp td{padding:4px 6px;border-bottom:1px solid #f0f2f5;vertical-align:top}.hp .thumb{width:44px;height:58px;object-fit:cover;border-radius:3px;vertical-align:middle;margin-right:6px;background:#d6dbe1}
.hp .btns{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px;align-items:center}.hp button{font:inherit;font-size:13.5px;padding:6px 12px;border-radius:8px;border:1px solid #b8c1cb;background:#fff;cursor:pointer;min-height:34px}
.hp button.p{background:#1f5fbf;color:#fff;border-color:#1f5fbf}.hp button.w{color:#a61b1b;border-color:#e3a0a0}.hp button.arm{background:#fff3d6;border-color:#e3a008;color:#6b4500}.hp button.done{background:#e3f6ec;border-color:#9fd8b6;color:#11683a}
.hp .small{font-size:12.5px;color:#5b6773}.hp .pick label{display:block;padding:3px 0;font-size:13.5px;cursor:pointer}.hp .ok{color:#17683a;font-weight:600}
</style>"""
PJS = """<script>
function hpTwo(b,body){if(b.classList.contains("done")||b.dataset.busy)return;
 if(!b.classList.contains("arm")){b.dataset.t=b.dataset.t||b.textContent;b.classList.add("arm");b.textContent=b.dataset.t+" — tap again";setTimeout(function(){if(b.classList.contains("arm")){b.classList.remove("arm");b.textContent=b.dataset.t;}},4000);return;}
 b.classList.remove("arm");b.dataset.busy="1";b.textContent="…";
 var box=b.closest(".hp");if(body.pick){var r=box&&box.querySelector('input[name="'+body.pick+'"]:checked');if(!r){delete b.dataset.busy;b.classList.remove("arm");b.textContent=b.dataset.t+" — pick a line first";return;}body.pl=r.value;}
 fetch("/finance/sanjeevni/api/needs-you/act",{method:"POST",credentials:"same-origin",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)})
 .then(function(r){return r.json().then(function(j){return [r.status,j];});}).then(function(x){delete b.dataset.busy;
  if(x[1]&&x[1].ok){b.classList.add("done");b.textContent="✓ "+(x[1].said||b.dataset.t);var row=b.closest(".btns");if(row)row.querySelectorAll("button").forEach(function(o){if(o!==b)o.disabled=true;});var li=b.closest("li");if(li&&x[1].gone)li.classList.add("s927-gone");}
  else{b.textContent=b.dataset.t+" — "+((x[1]&&(x[1].message||x[1].error))||"not saved");}})
 .catch(function(){delete b.dataset.busy;b.textContent=b.dataset.t+" — not saved";});}
</script>"""


def panel(con, kind, ref, who):
    try:
        if kind == "porders":
            return _panel_porders(con)
        if kind == "arrived":
            return _panel_arrived(con, int(ref or 0))
        if kind == "tapped":
            return _panel_tapped(con, str(ref or ""))
        if kind == "voucher":
            return _panel_voucher(con, str(ref or ""))
        if kind == "expiry":
            return _panel_expiry(con)
        if kind == "seen":
            return _panel_seen(str(request.args.get("text") or ""))
        return '<div class="hp"><div class="small">This line has no inline panel yet; the arrow opens its page.</div></div>'
    except Exception as e:                                        # noqa: BLE001
        print("S927 panel %s failed: %r" % (kind, e), file=sys.stderr)
        return '<div class="hp"><div class="small">The panel could not be built just now (%s); the arrow opens its page.</div></div>' % esc(str(e)[:80])


def _panel_porders(con):
    import order_flow as OF                                       # noqa: PLC0415
    con.row_factory = sqlite3.Row
    G = OF.groups(con, dt.datetime.now())
    return ('<div class="hp of">%s%s%s<div style="margin-top:6px">%s</div>%s</div>' % (
        OF.CSS, OF.JS, PJS, OF.team_table_s926(con, G["team"], "you", G), ""))


def _scan_lines(sid):
    try:
        import provisional_s781 as PV                             # noqa: PLC0415
        return PV.scan_lines(int(sid)) or []
    except Exception:                                             # noqa: BLE001
        return []


def _panel_arrived(con, lid):
    con.row_factory = sqlite3.Row
    l = con.execute("SELECT l.id, l.item, l.packs, l.pack_size, l.supplied, l.arrived_at, l.arrived_by, l.billed_bill_no, o.id AS oid, o.vendor, o.supplier_norm, "
                    "o.created_at FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id WHERE l.id=?", (lid,)).fetchone()
    if not l:
        return '<div class="hp"><div class="small">This order line is no longer there.</div></div>'
    l = dict(l)
    if l.get("billed_bill_no"):
        return '<div class="hp"><div class="ok">Settled: Marg bill %s carries it now.</div></div>' % esc(l["billed_bill_no"])
    ties = [dict(r) for r in con.execute("SELECT asset_bill_id, stamp, scan_at, how, arrived FROM order_scan_tie WHERE order_id=? ORDER BY tied_at", (l["oid"],))]
    since = str(l.get("arrived_at") or l.get("created_at") or "")[:10]
    low = (dt.date.fromisoformat(since) - dt.timedelta(days=3)).isoformat() if since else "2000-01-01"
    sn = l.get("supplier_norm") or _norm(l.get("vendor"))
    pls = [dict(r) for r in con.execute("SELECT id, item, qty, free, bill_no, bill_date, packing FROM purchase_line WHERE supplier_norm=? AND bill_date>=? AND "
                                        "UPPER(COALESCE(direction,'PURCHASE'))='PURCHASE' ORDER BY bill_date, bill_no, id LIMIT 400", (sn, low))]
    k = _norm(l["item"])
    same = [p for p in pls if _norm(p["item"]) == k]
    stock = ""
    try:
        import order_flow as OF                                   # noqa: PLC0415
        idn = OF.identity(con)
        nm, st, dead = OF._marg_stock(idn, l["item"])
        stock = "%s%s" % (st or "—", (" (as %s)" % nm) if dead else "")
    except Exception:                                             # noqa: BLE001
        pass
    h = ['<div class="hp">', PCSS, PJS]
    h.append('<div class="box"><b>%s</b> · ordered %s from %s · %d %s · counted as arrived %s %s · Marg stock today <b>%s</b></div>' % (
        esc(l["item"]), esc(ddmm(l["created_at"])), esc(l["vendor"]), int(l.get("packs") or 0), "pack" if int(l.get("packs") or 0) == 1 else "packs",
        esc(str(l.get("arrived_at") or "")[:16].replace("T", " ")), ("by %s" % esc(l["arrived_by"])) if l.get("arrived_by") and l["arrived_by"] != "scan" else "(the bill was scanned)", esc(stock)))
    if ties:
        h.append('<div class="box"><b>The scan%s</b>' % ("s" if len(ties) > 1 else ""))
        for t in ties:
            sid = int(t["asset_bill_id"])
            h.append('<div style="margin-top:4px"><a href="/scanapp/bills/%d/file" target="_blank" rel="noopener"><img class="thumb" loading="lazy" src="/scanapp/bills/%d/thumb" alt=""></a>'
                     '%s · scanned %s · <a href="/scanapp/bills/%d/file" target="_blank" rel="noopener">open full size →</a></div>' % (sid, sid, esc(t.get("stamp") or "#%d" % sid), esc(str(t.get("scan_at") or "")[:16].replace("T", " ")), sid))
            rl = _scan_lines(sid)
            if rl:
                h.append("<table><tr><th>Line read on the scan</th><th>Qty</th><th>Pack</th></tr>")
                for x in rl[:40]:
                    mine = _norm(x.get("name")) == k
                    h.append("<tr%s><td>%s%s</td><td>%s</td><td>%s</td></tr>" % (' style="background:#fff8e1"' if mine else "", esc(x.get("name")), " ← this medicine" if mine else "",
                                                                             esc(x.get("qty") if x.get("qty") is not None else ""), esc(x.get("pack") or "")))
                h.append("</table>")
                if not any(_norm(x.get("name")) == k for x in rl):
                    h.append('<div class="small">The scan\'s read lines do not carry this medicine by this name — a different size or spelling, or it was not on the bill.</div>')
            else:
                h.append('<div class="small">No lines read from this scan.</div>')
        h.append("</div>")
    else:
        h.append('<div class="box"><div class="small">No scan tied to this order.</div></div>')
    h.append('<div class="box"><b>Marg\'s purchases from %s since %s</b> (%d lines)' % (esc(l["vendor"]), esc(ddmm(low)), len(pls)))
    if pls:
        h.append('<table class="pick"><tr><th></th><th>Marg item</th><th>Qty</th><th>Bill</th><th>Date</th></tr>')
        for p in pls[:60]:
            mine = _norm(p["item"]) == k
            h.append('<tr%s><td><input type="radio" name="pl%d" value="%d"></td><td>%s%s</td><td>%s%s</td><td>%s</td><td>%s</td></tr>' % (
                ' style="background:#fff8e1"' if mine else "", int(l["id"]), int(p["id"]), esc(p["item"]), " ← same name" if mine else "", esc(p.get("qty")),
                (" +%s" % esc(p["free"])) if p.get("free") else "", esc(p.get("bill_no")), esc(ddmm(p.get("bill_date")))))
        h.append("</table>")
        if same:
            h.append('<div class="small">Marg DOES carry this name since the arrival (%s) — the match was missed; pick that line below and the order line is marked billed.</div>' % esc(", ".join("bill %s %s" % (p["bill_no"], ddmm(p["bill_date"])) for p in same[:3])))
        else:
            h.append('<div class="small">No Marg line of this name from this dealer since the arrival: either Amir never entered it, it came under another name (pick that line), or it never came.</div>')
    else:
        h.append('<div class="small">No Marg purchase from this dealer since the arrival at all.</div>')
    h.append("</div>")
    b = dict(lid=int(l["id"]))
    h.append('<div class="btns">%s%s%s</div>' % (
        _btn("Ask Amir to enter it (a job on his card)", dict(b, do="amir_ask"), "p"),
        _btn("It is this Marg line (picked above)", dict(b, do="marg_line", pick="pl%d" % int(l["id"]))),
        _btn("Never came — the line is short", dict(b, do="never_came"), "w")))
    h.append("</div>")
    return "".join(h)


def _panel_tapped(con, ref):
    con.row_factory = sqlite3.Row
    vendor, dm = (ref.split("|", 1) + [""])[:2]
    since = _since_from_ddmm(dm) if dm else ""
    rows = [dict(r) for r in con.execute("SELECT o.id, o.vendor, o.created_at, l.item, l.packs, l.supplied, l.arrived_by, l.arrived_at FROM purchase_order o JOIN purchase_order_line l ON l.order_id=o.id "
                                         "WHERE o.vendor=? AND substr(l.arrived_at,1,10)=? ORDER BY o.id, l.id", (vendor, since))]
    h = ['<div class="hp">', PCSS]
    if not rows:
        h.append('<div class="small">No tapped line of %s on %s is left.</div></div>' % (esc(vendor), esc(dm)))
        return "".join(h)
    h.append('<div class="box"><b>%s</b> · tapped as arrived %s by %s · order of %s<table><tr><th>Medicine</th><th>Ordered</th><th>Tapped came</th></tr>%s</table>'
             '<div class="small">No bill scanned from %s since, nothing in Marg. Reception scans the bill when it turns up (the Aaya row on her strip); until then this is for your eyes.</div></div></div>' % (
                 esc(vendor), esc(dm), esc(rows[0].get("arrived_by") or "staff"), esc(ddmm(rows[0]["created_at"])),
                 "".join("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (esc(r["item"]), esc(r["packs"]), esc(r["supplied"])) for r in rows), esc(vendor)))
    return "".join(h)


def _panel_voucher(con, item):
    con.row_factory = sqlite3.Row
    k = _norm(item)
    jobs = [dict(r) for r in con.execute("SELECT key, text_hi, created_at, created_by, done_at, said_what FROM amir_job WHERE subject=? ORDER BY id DESC LIMIT 5", (item,))]
    h = ['<div class="hp">', PCSS, PJS, '<div class="box"><b>%s</b> — the count\'s voucher is not in Marg\'s closings.' % esc(item)]
    if jobs:
        h.append("<table><tr><th>Job on Amir's card</th><th>Made</th><th>Amir</th></tr>")
        for j in jobs:
            h.append("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (esc(j["text_hi"]), esc(ddmm(j["created_at"])), ("tapped done %s%s" % (ddmm(j["done_at"]), (" — " + esc(j["said_what"])) if j.get("said_what") else "")) if j.get("done_at") else "open"))
        h.append("</table>")
        if any(j.get("done_at") for j in jobs):
            h.append('<div class="small">Amir tapped done, yet Marg\'s closings show no move — the voucher was not entered, or entered on another item.</div>')
    else:
        h.append('<div class="small">No job for this voucher on Amir\'s card yet.</div>')
    h.append("</div>")
    h.append('<div class="btns">%s</div>' % _btn("Ask Amir again (a job on his card, marked: Marg shows no move)", dict(do="voucher_again", item=item), "p"))
    h.append('<div class="small">Accepting Marg\'s figure (withdrawing the voucher) belongs to the Stock check page, built next.</div></div>')
    return "".join(h)


def _panel_expiry(con):
    con.row_factory = sqlite3.Row
    r = con.execute("SELECT id, today FROM stock_expiry_run WHERE ok=1 ORDER BY id DESC LIMIT 1").fetchone()
    h = ['<div class="hp">', PCSS]
    if not r:
        return "".join(h + ['<div class="small">No expiry run yet.</div></div>'])
    rows = [dict(x) for x in con.execute("SELECT item, batch, expiry, units, pack, packing, section FROM stock_expiry_line WHERE run_id=? ORDER BY seq LIMIT 60", (int(r["id"]),))]
    h.append('<div class="box"><b>Expiry watch</b> · run of %s · %d batches<table><tr><th>Medicine</th><th>Batch</th><th>Expiry</th><th>Units</th><th>Section</th></tr>%s</table>'
             '<div class="small"><a href="/finance/sanjeevni/expiry">the expiry page → (the taps are there)</a></div></div></div>' % (
                 esc(r["today"]), len(rows), "".join("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (esc(x["item"]), esc(x["batch"]), esc(x["expiry"]), esc(x["units"]), esc(x["section"])) for x in rows)))
    return "".join(h)


def _panel_seen(text):
    return '<div class="hp">%s%s<div class="small">For your information — nothing to do.</div><div class="btns">%s</div></div>' % (
        PCSS, PJS, _btn("Seen — not shown again for 30 days", dict(do="seen", text=text), ""))


# ------------------------------------------------------------------ the doors
def _audit(con, who, action, ref, detail):
    try:
        import order_sheet                                        # noqa: PLC0415
        order_sheet.audit(con, who, action, ref, dict(detail, kit=KIT))
    except Exception:                                             # noqa: BLE001
        pass


def _amir_job(con, who, key, subject, text_hi, sub_hi):
    ts = now_iso()
    if con.execute("SELECT 1 FROM amir_job WHERE key=?", (key,)).fetchone():
        return False
    con.execute("INSERT INTO amir_job (key, kind, subject, text_hi, sub_hi, created_at, created_by, show_from) VALUES (?,?,?,?,?,?,?,?)",
                (key, "tap", subject, text_hi, sub_hi, ts, "S927 (the owner's word, %s)" % ts[:16].replace("T", " "), ts))
    return True


def act(con, who, b):
    """His doors; any unexpected fault rolls the connection back and answers 500 -- nothing half-written waits for the next request's commit."""
    try:
        return _act(con, who, b)
    except Exception as e:                                        # noqa: BLE001
        try:
            con.rollback()
        except Exception:                                         # noqa: BLE001
            pass
        print("S927 act failed: %r" % (e,), file=sys.stderr)
        return dict(ok=False, error="failed", message=str(e)[:120]), 500


def _act(con, who, b):
    ensure(con)
    con.row_factory = sqlite3.Row
    do = str(b.get("do") or "")
    if do == "seen":
        text = str(b.get("text") or "")
        if not text:
            return dict(ok=False, error="bad_request"), 400
        until = (dt.date.today() + dt.timedelta(days=SEEN_DAYS)).isoformat()
        con.execute("INSERT INTO hub_seen (key, text, until, by, at) VALUES (?,?,?,?,?)", (_key(text), text[:400], until, who, now_iso()))
        con.commit()
        return dict(ok=True, gone=True, said="Seen — back after %s" % ddmm(until)), 200
    if do in ("amir_ask", "marg_line", "never_came"):
        try:
            lid = int(b.get("lid") or 0)
        except (TypeError, ValueError):
            return dict(ok=False, error="bad_request"), 400
        l = con.execute("SELECT l.id, l.item, l.packs, l.pack_size, l.supplied, l.arrived_at, l.billed_bill_no, o.id AS oid, o.vendor, o.supplier_norm, o.created_at "
                        "FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id WHERE l.id=?", (lid,)).fetchone()
        if not l:
            return dict(ok=False, error="gone", message="This order line is no longer there."), 409
        l = dict(l)
        if l.get("billed_bill_no"):
            return dict(ok=False, error="settled", message="Marg bill %s already carries it." % l["billed_bill_no"]), 409
        t = now_iso()
        if do == "amir_ask":
            tie = con.execute("SELECT stamp FROM order_scan_tie WHERE order_id=? ORDER BY tied_at DESC LIMIT 1", (l["oid"],)).fetchone()
            made = _amir_job(con, who, "S927:arr:%d" % lid, l["item"],
                             "%s — %s ka bill (%s) Marg mein daaliye" % (l["item"], l["vendor"], ddmm(l.get("arrived_at") or l["created_at"])),
                             "Order %s ka maal %s aaya (scan %s) par Marg ki purchase mein nahi hai. Daal kar 'Kar diya' dabaiye." % (
                                 ddmm(l["created_at"]), ddmm(l.get("arrived_at") or ""), (tie[0] if tie else "—")))
            _audit(con, who, "s927_amir_ask", str(lid), dict(item=l["item"], made=made))
            con.commit()
            return dict(ok=True, said="On Amir's card" + ("" if made else " (already)")), 200
        if do == "never_came":
            con.execute("UPDATE purchase_order_line SET supplied=0, short=1, arrived_by=?, arrived_at=COALESCE(arrived_at, ?) WHERE id=?", ("owner:never_came", t, lid))
            _audit(con, who, "s927_never_came", str(lid), dict(item=l["item"], was_supplied=l.get("supplied")))
            con.commit()
            return dict(ok=True, gone=True, said="Never came — the line reads short; it carries as a shortage"), 200
        try:
            pid = int(b.get("pl") or 0)
        except (TypeError, ValueError):
            pid = 0
        p = con.execute("SELECT id, item, qty, free, bill_no, bill_date, supplier_norm FROM purchase_line WHERE id=?", (pid,)).fetchone()
        if not p:
            return dict(ok=False, error="bad_request", message="Pick the Marg line first."), 400
        p = dict(p)
        if p["supplier_norm"] != (l.get("supplier_norm") or _norm(l.get("vendor"))):
            return dict(ok=False, error="other_dealer", message="That line is another dealer's."), 409
        q = int(float(p.get("qty") or 0) + float(p.get("free") or 0))
        con.execute("UPDATE purchase_order_line SET billed_qty=?, billed_bill_no=?, billed_date=?, detected_at=?, billed_units=NULL WHERE id=?",
                    (max(q, 0), str(p["bill_no"] or ""), p["bill_date"], t, lid))
        if l.get("supplied") is None:
            con.execute("UPDATE purchase_order_line SET supplied=?, short=? WHERE id=?", (max(q, 0), 1 if q < int(l.get("packs") or 0) else 0, lid))
        learnt = ""
        if _norm(p["item"]) != _norm(l["item"]):
            try:
                import med_names as MN                            # noqa: PLC0415
                MN.ensure(con)
                MN._put(con, "marg", "", p["item"], l["item"], "yes", dict(kit=KIT, by=who, why="owner picked the Marg line on the Hub"), dt.datetime.now())
                learnt = "; %s = %s learnt" % (p["item"], l["item"])
            except Exception:                                     # noqa: BLE001
                pass
        _audit(con, who, "s927_marg_line", str(lid), dict(item=l["item"], marg_item=p["item"], bill=p["bill_no"], qty=q))
        con.commit()
        return dict(ok=True, gone=True, said="Marked billed on %s%s" % (p["bill_no"], learnt)), 200
    if do == "voucher_again":
        item = str(b.get("item") or "").strip()
        if not item:
            return dict(ok=False, error="bad_request"), 400
        made = _amir_job(con, who, "S927:voucher:%s:%s" % (_norm(item), dt.date.today().isoformat()), item,
                         "%s — ginti ka voucher Marg mein daaliye (Marg mein abhi tak move nahi dikha)" % item,
                         "Pehle 'Kar diya' daba diya tha, par Marg ki closing mein yeh move nahi aaya. Dobara dekh kar daaliye, phir 'Kar diya'.")
        _audit(con, who, "s927_voucher_again", item, dict(made=made))
        con.commit()
        return dict(ok=True, said="On Amir's card" + ("" if made else " (already today)")), 200
    return dict(ok=False, error="bad_do"), 400


# ------------------------------------------------------------------ the routes
@bp.route("/finance/sanjeevni/api/needs-you/panel")
def r_panel():
    u, err = _require("checker")
    if err:
        return err
    con = _db()
    kind, ref = str(request.args.get("kind") or ""), str(request.args.get("ref") or "")
    return panel(con, kind, ref, str(u.get("user") or "")), 200, {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store"}


@bp.route("/finance/sanjeevni/api/needs-you/act", methods=["POST"])
def r_act():
    u, err = _require("checker")
    if err:
        return err
    con = _db()
    b = request.get_json(silent=True)
    if not isinstance(b, dict):
        return jsonify(ok=False, error="bad_request"), 400
    r, st = act(con, str(u.get("user") or ""), b)
    return jsonify(**r), st


@bp.route("/finance/sanjeevni/api/needs-you/healthz")
def r_healthz():
    return jsonify(ok=True, module="hub_panels", version=VERSION, kit=KIT)
