#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s431.py -- builds the patched live files of kit S431_COUNT_STATEMENT from the LIVE bytes by anchored edits. Every anchor must
occur exactly once and every source must be at its FROM pin, or the build stops with nothing written. (stock_statement.py and
stock_statement.html are new, shipped in the kit.)

  stock_app.py       stock_statement imported defensively (the S418 way); the report's links carry the statement; the hub's links carry
                     the statement (live and the latest frozen copy); the statement routes: /page/statement, /api/statement/<cid>[.pdf|.xlsx],
                     /api/statement/<cid>/freeze, /api/statement/frozen/<sid>.pdf|.xlsx|.json
  stock_hub.html     the first card gains "The count statement -- section by section" (page / PDF / Excel, the frozen copy "as at");
                     the status card names the S430 groups (old stock, owner's use)
  stock_report.html  the "N lines still need a word / decision desk" block becomes "closed on <date> -- see the statement"; a statement link

Usage: make_s431.py --finance /root/finance --out DIR
"""
import argparse
import hashlib
import os
import sys

FROM = {
    "stock_app.py": "0e0fc043c4bbae75c6f1fc8149547cb7",
    "stock_hub.html": "74ea06997b900e9f55c47dca473a9232",
    "stock_report.html": "bd750dc8a32c0ed6baf66f48d7114c90",
}


def md5(b):
    return hashlib.md5(b).hexdigest()


def load(path, name):
    raw = open(path, "rb").read()
    if md5(raw) != FROM[name]:
        sys.exit("REFUSED: %s is %s, not its FROM pin %s" % (path, md5(raw), FROM[name]))
    return raw.decode("utf-8")


def rep(s, old, new, what, count=1):
    n = s.count(old)
    if n != count:
        sys.exit("REFUSED: anchor for %s found %d times (need exactly %d): %r" % (what, n, count, old[:90]))
    return s.replace(old, new)


IMPORT_BLOCK = '''# --- S428_STOCK_WATCH end --------------------------------------------------

# --- S431_COUNT_STATEMENT begin ---------------------------------------------
# The count as ONE statement, section by section, at selling price (stock_statement.py beside this file). Defensive: without
# it every page behaves exactly as before S431.
try:
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import stock_statement as _ss                          # noqa: PLC0415
    STOCK_STATEMENT_OK = True
except Exception:                                          # pragma: no cover
    _ss = None
    STOCK_STATEMENT_OK = False
# --- S431_COUNT_STATEMENT end -----------------------------------------------
'''

ROUTES = r'''
# ---- S431_COUNT_STATEMENT begin ---------------------------------------------------
# The owner, 27-Sep-2026: "Better it be section-wise ... the complete list of 6th Sept with Marg stock, physical stock and
# shortages, and the excess items removed and matched; the orthotics at selling price. Give me a link." The owner's and the
# doctor's pages (stock_statement.DOCTORS); staff never. Freeze = the S227 discipline: a kept copy, dated, fingerprinted.
def _statement_gate():
    u, err = _require("checker", "viewer")
    if err:
        return None, None, err
    if not STOCK_STATEMENT_OK:
        return None, None, (jsonify(ok=False, error="unavailable", message="stock_statement.py is not beside stock_app.py"), 503)
    if not _ss.may_read(u):
        return None, None, (jsonify(ok=False, error="forbidden", message="This page is the owner's and the doctor's."), 403)
    con = _db()
    ensure_schema(con)
    _pad_ensure(con)
    _ss.ensure(con)
    return u, con, None


@bp.route("/page/statement")
def page_statement():
    u, con, err = _statement_gate()
    if err:
        return err
    from flask import Response                                # noqa: PLC0415
    cid = request.args.get("count", "").strip()
    if not cid.isdigit():
        cid = str(_newest_root(con) or 0)
    try:
        with io.open(_ss.PAGE, "r", encoding="utf-8") as fh:
            html = fh.read()
    except IOError:
        return jsonify(ok=False, error="missing", message="stock_statement.html is not beside stock_app.py"), 503
    boot = json.dumps(dict(count_id=int(cid), user=(u or {}).get("user") or "", can_freeze=_may_decide(u)))
    return Response(html.replace("/*__BOOT__*/", "window.BOOT=" + boot + ";"), mimetype="text/html")


@bp.route("/api/statement/<int:cid>")
def api_statement(cid):
    u, con, err = _statement_gate()
    if err:
        return err
    d = _pad_report_data(con, cid)
    if d is None:
        return jsonify(ok=False, error="not_found", message="No count #%d." % cid), 404
    S = _ss.build(con, d)
    return jsonify(ok=True, frozen_list=_ss.frozen_list(con, d["count_id"]), you=dict(user=(u or {}).get("user") or ""), **S)


@bp.route("/api/statement/<int:cid>.pdf")
def api_statement_pdf(cid):
    u, con, err = _statement_gate()
    if err:
        return err
    from flask import Response                                # noqa: PLC0415
    d = _pad_report_data(con, cid)
    if d is None:
        return jsonify(ok=False, error="not_found", message="No count #%d." % cid), 404
    return Response(_ss.render_pdf(_ss.build(con, d)), mimetype="application/pdf",
                    headers={"Content-Disposition": 'inline; filename="COUNT_STATEMENT_count%d_live.pdf"' % d["count_id"], "Cache-Control": "no-store"})


@bp.route("/api/statement/<int:cid>.xlsx")
def api_statement_xlsx(cid):
    u, con, err = _statement_gate()
    if err:
        return err
    d = _pad_report_data(con, cid)
    if d is None:
        return jsonify(ok=False, error="not_found", message="No count #%d." % cid), 404
    return _xlsx_response(_ss.render_xlsx(_ss.build(con, d)), "COUNT_STATEMENT_count%d_live.xlsx" % d["count_id"])


@bp.route("/api/statement/<int:cid>/freeze", methods=["POST"])
def api_statement_freeze(cid):
    """One tap (the owner): the statement as it stands -> a frozen row with its PDF and XLSX."""
    u, con, err = _statement_gate()
    if err:
        return err
    if not _may_decide(u):
        return jsonify(ok=False, error="forbidden", message="Only the owner freezes a statement."), 403
    d = _pad_report_data(con, cid)
    if d is None:
        return jsonify(ok=False, error="not_found", message="No count #%d." % cid), 404
    f = _ss.freeze(con, d, (u or {}).get("user") or "")
    return jsonify(ok=True, message="Frozen as at %s IST (fingerprint %s)." % (f["made_text"], f["md5"][:8]), frozen=f)


@bp.route("/api/statement/frozen/<int:sid>.<kind>")
def api_statement_frozen(sid, kind):
    u, con, err = _statement_gate()
    if err:
        return err
    from flask import Response                                # noqa: PLC0415
    if kind not in ("pdf", "xlsx", "json"):
        return jsonify(ok=False, error="bad_request", message="pdf, xlsx or json"), 400
    if kind == "json":
        f = _ss.frozen_row(con, sid, with_data=True)
        if not f:
            return jsonify(ok=False, error="not_found", message="No such statement."), 404
        return jsonify(ok=True, **f)
    data, f = _ss.frozen_file(con, sid, kind)
    if data is None:
        return jsonify(ok=False, error="not_found", message="No such statement."), 404
    if kind == "pdf":
        return Response(data, mimetype="application/pdf", headers={"Content-Disposition": 'inline; filename="COUNT_STATEMENT_count%d_%s.pdf"' % (f["count_id"], f["md5"][:8])})
    return _xlsx_response(data, "COUNT_STATEMENT_count%d_%s.xlsx" % (f["count_id"], f["md5"][:8]))


def _statement_links_safe(con, root):
    if not STOCK_STATEMENT_OK:
        return dict(statement=None, statement_pdf=None, statement_xlsx=None, statement_frozen=None)
    try:
        return dict(statement="/finance/stock/page/statement?count=%d" % root, statement_pdf="/finance/stock/api/statement/%d.pdf" % root,
                    statement_xlsx="/finance/stock/api/statement/%d.xlsx" % root, statement_frozen=_ss.frozen_latest_links(con, root))
    except Exception:                                          # noqa: BLE001
        return dict(statement="/finance/stock/page/statement?count=%d" % root, statement_pdf=None, statement_xlsx=None, statement_frozen=None)
# ---- S431_COUNT_STATEMENT end -----------------------------------------------------
'''


def build_stock_app(s):
    s = rep(s, "# --- S428_STOCK_WATCH end --------------------------------------------------\n", IMPORT_BLOCK, "import stock_statement")
    s = rep(s, '''                           loss_page="/finance/stock/page/loss?count=%d" % _root,
''', '''                           loss_page="/finance/stock/page/loss?count=%d" % _root,
                           statement="/finance/stock/page/statement?count=%d" % _root,   # S431
''', "the report's statement link")
    s = rep(s, '''                links=dict(report="/finance/stock/page/report?count=%d" % root, diffs_pdf=d["links"]["diffs_pdf"],
                           desk="/finance/stock/page/desk?count=%d" % root, loss=d["links"]["loss_page"],
''', '''                links=dict(report="/finance/stock/page/report?count=%d" % root, diffs_pdf=d["links"]["diffs_pdf"],
                           desk="/finance/stock/page/desk?count=%d" % root, loss=d["links"]["loss_page"],
                           **_statement_links_safe(con, root),                # S431: the statement (live) and its latest frozen copy
''', "the hub's statement links")
    s = rep(s, "# ---- S428_STOCK_WATCH end -----------------------------------------------------------\n",
            "# ---- S428_STOCK_WATCH end -----------------------------------------------------------\n" + ROUTES.lstrip("\n"), "the S431 routes")
    return s


def build_hub(s):
    s = rep(s, '''    +'<div class="links"><a class="b" href="'+esc(L.report)+'">The count — full report</a><a class="b" href="'+esc(L.diffs_pdf)+'" target="_blank" rel="noopener">All differences (PDF, your copy)</a></div></div>';
''', '''    +(L.statement?'<div class="links"><a class="b main" href="'+esc(L.statement)+'">The count statement — section by section</a>'+(L.statement_pdf?'<a class="b" href="'+esc(L.statement_pdf)+'" target="_blank" rel="noopener">Statement (PDF)</a><a class="b" href="'+esc(L.statement_xlsx)+'">Statement (Excel)</a>':'')
      +(L.statement_frozen?'<span class="sub" style="align-self:center">frozen as at '+esc(L.statement_frozen.as_at)+' · <a href="'+esc(L.statement_frozen.pdf)+'" target="_blank" rel="noopener">PDF</a> · <a href="'+esc(L.statement_frozen.xlsx)+'">Excel</a></span>':'')+'</div>':'')   /* S431 */
    +'<div class="links"><a class="b" href="'+esc(L.report)+'">The count — full report</a><a class="b" href="'+esc(L.diffs_pdf)+'" target="_blank" rel="noopener">All differences (PDF, your copy)</a></div></div>';
''', "the first card's statement links")
    s = rep(s, '''["consume","clinic consumption"],["big","big loss"],["owner","your choice"],["earlier","before the piles"]]''',
            '''["old","old stock"],["consume","clinic consumption"],["owner_use","owner's use"],["big","big loss"],["owner","your choice"],["earlier","before the piles"]]''', "the status card's S430 groups")
    return s


def build_report(s):
    s = rep(s, '''  if(B.checker) b+='<div class="card owner noprint" id="s0"><b>'+((d.totals||{}).open||0)+' line'+((d.totals||{}).open===1?'':'s')+' still need'+((d.totals||{}).open===1?'s':'')+' a word'+(need.length?' — '+need.length+' of them yours alone':'')+'.</b> <a class="desk" href="'+esc(BASE+"/page/desk?count="+d.count_id)+'">Open the decision desk →</a><div class="sub">One card at a time, one question, big buttons. This page is the document.</div></div>';
''', '''  if(B.checker) b+='<div class="card owner noprint" id="s0"><b>'+(d.closed?('Closed on '+esc(d.closed.at_text||"")+(d.closed.by?' by '+esc(d.closed.by):'')+' — see the statement.'):'The count is open.')+'</b> <a class="desk" href="'+esc(d.links.statement||(BASE+"/page/statement?count="+d.count_id))+'">The count statement — section by section →</a><div class="sub">Every counted line once, in three sections, at selling price; the orthotics apart. This page stays as the document of the count.</div></div>';   /* S431: the decision desk left this page */
''', "the decision-desk block")
    s = rep(s, '''  h+='<div class="tools"><button type="button" onclick="window.print()">Print / save as PDF</button>'
''', '''  h+='<div class="tools"><button type="button" onclick="window.print()">Print / save as PDF</button>'
    +'<a href="'+esc(d.links.statement||(BASE+"/page/statement?count="+d.count_id))+'"><b>The count statement — section by section</b></a>'   /* S431 */
''', "the tools' statement link")
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    src = {name: load(os.path.join(a.finance, name), name) for name in FROM}
    out = {"stock_app.py": build_stock_app(src["stock_app.py"]), "stock_hub.html": build_hub(src["stock_hub.html"]), "stock_report.html": build_report(src["stock_report.html"])}
    os.makedirs(a.out, exist_ok=True)
    for name, text in out.items():
        b = text.encode("utf-8")
        with open(os.path.join(a.out, name), "wb") as fh:
            fh.write(b)
        print("%s  %s" % (md5(b), name))


if __name__ == "__main__":
    main()
