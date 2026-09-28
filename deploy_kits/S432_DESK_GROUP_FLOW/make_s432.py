#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s432.py -- builds the patched live files of kit S432_DESK_GROUP_FLOW from the LIVE bytes by anchored edits. Every anchor must
occur exactly once and every source must be at its FROM pin, or the build stops with nothing written. (loss_piles.py v2.2,
stock_watch.py v1.2, stock_loss.html and qty_words.py v1.1 are whole files shipped in the kit; the installer pins their FROM too.)

  stock_app.py           the desk read serves the pile CACHE (loss_piles.desk_cached: ?lite=1 for the totals first, ?pile=<key> for one
                         pile's lines) and the STORED watch (stock_watch.stored_owner_view) -- no report, no sales test, no trace, no
                         scoring on the read path; move / accept return the PATCH (the changed line + the totals); the close opens the
                         Big-loss traces (once) and returns the patch; NEW doors: POST /api/loss/<cid>/pile/clear (arm {group, items} ->
                         confirm {token}: the ticked lines written off as that group; the last clear closes the count by itself) and
                         POST /api/watch/refresh (the watch scored again, stored).
  stock_statement.py     3.4: a NEGATIVE Marg balance is a book correction, no goods -- tagged, its quantity to correct shown as such,
                         EXCLUDED from the section's excess money, counted in its own line under the section totals; the PDF and the
                         XLSX follow (the Marg column shows the minus through qty_words v1.1).
  stock_statement.html   the Marg-negative line under the totals; the row's Excess cell reads 'N pcs to correct'.

Usage: make_s432.py --finance /root/finance --out DIR
"""
import argparse
import hashlib
import os
import sys

FROM = {
    "stock_app.py": "2a95e2543330b3efbdb0dc0106892bea",
    "stock_statement.py": "85ec7619d79c7a9f311f7bed91eeabae",
    "stock_statement.html": "175f4654a88e6bb81d0fd724be6d93c4",
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


# ---------------------------------------------------------------- stock_app.py
PILES_OLD = '''    _lp.sales_test(con, _desk_root(con, cid) or cid)           # S427 (3.4): sold after the count -> the stock existed; closed by the system before piling
    d = _pad_report_data(con, cid)
    if d is None:
        return jsonify(ok=False, error="not_found", message="No count #%d." % cid), 404
    out = _lp.desk(con, d, (u or {}).get("user") or "")
    if STOCK_WATCH_OK:                                          # S428 (D633): a trace on every Big-loss line; the owner's watch card
        _sw.trace_big_losses(con, d["count_id"], [l for p in out["piles"] for l in p["lines"]], (u or {}).get("user") or "")
        out["watch"] = _sw.owner_view(con, d["count_id"])
    return jsonify(ok=True, you=dict(user=(u or {}).get("user") or ""), **out)
'''
PILES_NEW = '''    # S432 (F-651): the desk from the PILE CACHE -- no report, no sales test, no trace and no watch scoring on the read path.
    # ?lite=1 gives the totals, the piles' headers, the close and the block first; ?pile=<key> gives one pile's lines; ?rebuild=1
    # recomputes everything once. The watch card is the STORED view (the 06:30 job / 'Refresh watch'), with its time.
    root = _desk_root(con, cid)
    if root is None:
        return jsonify(ok=False, error="not_found", message="No count #%d." % cid), 404
    lite = str(request.args.get("lite") or "").strip() in ("1", "true", "yes")
    pile = str(request.args.get("pile") or "").strip() or None
    force = str(request.args.get("rebuild") or "").strip() in ("1", "true", "yes")
    out = _lp.desk_cached(con, root, (u or {}).get("user") or "", lite=lite, pile=pile, force=force)
    if out is None:
        return jsonify(ok=False, error="not_found", message="No count #%d." % cid), 404
    if STOCK_WATCH_OK:
        out["watch"] = _sw.stored_owner_view(con, root)
    return jsonify(ok=True, you=dict(user=(u or {}).get("user") or ""), **out)
'''
MOVE_OLD = '''    ok, msg, code = _lp.move(con, root, str(b.get("item") or "").strip(), str(b.get("pile") or "").strip(), (u or {}).get("user") or "")
    return jsonify(ok=ok, message=msg), code
'''
MOVE_NEW = '''    ok, msg, code, patch = _lp.move_patch(con, root, str(b.get("item") or "").strip(), str(b.get("pile") or "").strip(), (u or {}).get("user") or "")   # S432: the patch for the page
    return jsonify(ok=ok, message=msg, patch=patch), code
'''
ACCEPT_OLD = '''    ok, msg, code, n = _lp.accept(con, root, items[:200], who)
    return jsonify(ok=ok, message=msg, accepted=n), code
'''
ACCEPT_NEW = '''    ok, msg, code, n, patch = _lp.accept_patch(con, root, items[:200], who)   # S432: the patch for the page
    return jsonify(ok=ok, message=msg, accepted=n, patch=patch), code
'''
CLOSE_OLD = '''    ok, msg, code, done = _lp.close(con, root, b.get("token"), who)
    if ok and STOCK_WATCH_OK and (done or {}).get("run"):     # S428 (3.1): a closed full count writes one point per counted item
        _sw.full_count_points(con, root, None, who)
    return jsonify(ok=ok, message=msg, done=done), code
'''
CLOSE_NEW = '''    ok, msg, code, done = _lp.close(con, root, b.get("token"), who)
    if ok and STOCK_WATCH_OK and (done or {}).get("run"):     # S428 (3.1): a closed full count writes one point per counted item
        _sw.full_count_points(con, root, None, who)
        _sw.trace_big_losses(con, root, (done or {}).get("big_lines") or [], who)   # S432: a Big-loss trace is opened by the close, once -- not by reading
    return jsonify(ok=ok, message=msg, done=done), code
'''
ROUTES = r'''
# ---- S432_DESK_GROUP_FLOW begin (F-651) ------------------------------------------
# The owner, 27-Sep-2026: "I select a group -- a button to tick all -- all ticked; I individually then untick some, and on
# unticking a change-pile menu appears; the other ticked ones disappear on clicking the Clear-pile button." And: "The page
# opens real slow, and each tick takes a lot of time too." The desk read serves the pile cache (above); these are the two doors
# the S432 page adds: Clear this group (armed, the 10-second confirm, exactly the ticked lines, one run per clear; the last clear
# closes the count by itself -- the staff block, the S428 points, the traces) and Refresh watch (the watch scored again, stored).
@bp.route("/api/loss/<int:cid>/pile/clear", methods=["POST"])
def api_loss_pile_clear(cid):
    """First tap: {group, items} -> arms for loss_piles.ARM_SECONDS and returns a token. Second tap: {token} -> the ticked lines
    are written off NOW as that group (WRITE_OFF + closed, one stock_writeoff_run, Amir's vouchers in rounds, audited)."""
    u, con, err = _desk_gate()
    if err:
        return err
    err = _desk_owner_only(u)
    if err:
        return err
    b = request.get_json(silent=True) or {}
    root = _desk_root(con, cid)
    if root is None:
        return jsonify(ok=False, error="not_found", message="No count #%d." % cid), 404
    who = (u or {}).get("user") or ""
    if not b.get("token"):
        ok, msg, code, armed = _lp.arm_clear(con, root, who, str(b.get("group") or "").strip(), b.get("items") or [])
        return jsonify(ok=ok, message=msg, arm=armed), code
    ok, msg, code, done = _lp.clear(con, root, b.get("token"), who)
    if ok and STOCK_WATCH_OK and (done or {}).get("run"):
        if (done or {}).get("auto_closed"):                    # the last clear closed the count: the S428 points, once
            _sw.full_count_points(con, root, None, who)
        _sw.trace_big_losses(con, root, (done or {}).get("big_lines") or [], who)   # a Big-loss trace is opened by the clear, once
    return jsonify(ok=ok, message=msg, done=done), code


@bp.route("/api/watch/refresh", methods=["POST"])
def api_watch_refresh():
    """The owner's 'Refresh watch': the traces on the cached Big-loss lines and the watch scored again, stored with the time."""
    u, con, err = _watch_gate()
    if err:
        return err
    err = _desk_owner_only(u)
    if err:
        return err
    b = request.get_json(silent=True) or {}
    root = int(b.get("count_id") or 0) or (_newest_root(con) or 0)
    V = _sw.refresh_owner_view(con, root, (u or {}).get("user") or "")
    return jsonify(ok=True, message="Watch refreshed %s (%d ms%s)." % (V.get("stored_text") or "", V.get("refresh_ms") or 0,
                                                                        (", %d trace%s opened" % (V["traces_opened"], "" if V["traces_opened"] == 1 else "s")) if V.get("traces_opened") else ""), watch=V)
# ---- S432_DESK_GROUP_FLOW end --------------------------------------------------
'''


def build_stock_app(s):
    s = rep(s, PILES_OLD, PILES_NEW, "the desk read from the cache")
    s = rep(s, MOVE_OLD, MOVE_NEW, "the move door's patch")
    s = rep(s, ACCEPT_OLD, ACCEPT_NEW, "the accept door's patch")
    s = rep(s, CLOSE_OLD, CLOSE_NEW, "the close opens the traces")
    s = rep(s, "# ---- S431_COUNT_STATEMENT end -----------------------------------------------------\n",
            "# ---- S431_COUNT_STATEMENT end -----------------------------------------------------\n" + ROUTES.lstrip("\n"), "the S432 routes")
    return s


# ---------------------------------------------------------------- stock_statement.py (3.4: the negative-Marg lines)
ST_LINE_OLD = '''        if short or over_:
            out_sections[s]["lines"].append(L)
        else:
            L["became"] = L["became"] or ("swap confirmed -- no loss" if swapped else "matched")
            out_sections[s]["matched"].append(L)
'''
ST_LINE_NEW = '''        if marg < 0:                                              # S432 (3.4): a NEGATIVE Marg balance is a book correction, not goods
            correct = counted - marg                              # what brings Marg from below zero up to the shelf
            L.update(neg_marg=True, correct_units=correct, correct_text=qw(correct, pack, packing, item),
                     short=0, over=0, short_text="", over_text="", short_p=(0 if price else None), over_p=(0 if price else None),
                     became="Marg negative -- book correction, no goods: %s to correct" % qw(correct, pack, packing, item), became_key="neg")   # 'open' stays the section's own word
            out_sections[s]["lines"].append(L)
        elif short or over_:
            out_sections[s]["lines"].append(L)
        else:
            L["became"] = L["became"] or ("swap confirmed -- no loss" if swapped else "matched")
            out_sections[s]["matched"].append(L)
'''
ST_TOT_OLD = '''        T = dict(lines=len(ls) + len(S["matched"]), differing=len(ls), matched=len(S["matched"]),
                 short_lines=sum(1 for l in ls if l["short"]), over_lines=sum(1 for l in ls if l["over"]),
                 short_p=sum(l["short_p"] or 0 for l in ls), over_p=sum(l["over_p"] or 0 for l in ls),
                 unpriced=sum(1 for l in ls if l["price_p"] is None), unpriced_items=[l["item"] for l in ls if l["price_p"] is None],
'''
ST_TOT_NEW = '''        T = dict(lines=len(ls) + len(S["matched"]), differing=len(ls), matched=len(S["matched"]),
                 short_lines=sum(1 for l in ls if l["short"]), over_lines=sum(1 for l in ls if l["over"]),
                 short_p=sum(l["short_p"] or 0 for l in ls), over_p=sum(l["over_p"] or 0 for l in ls),
                 unpriced=sum(1 for l in ls if l["price_p"] is None and not l.get("neg_marg")), unpriced_items=[l["item"] for l in ls if l["price_p"] is None and not l.get("neg_marg")],
                 neg_lines=sum(1 for l in ls if l.get("neg_marg")), neg_items=[l["item"] for l in ls if l.get("neg_marg")],   # S432 (3.4): Marg negative -- book corrections, no goods, no excess money
                 neg_text="; ".join("%s %s" % (l["item"], l["correct_text"]) for l in ls if l.get("neg_marg")),
'''
ST_OVERALL_OLD = '''                   over_p=sum(S["totals"]["over_p"] for S in sections), unpriced=sum(S["totals"]["unpriced"] for S in sections))
    overall["net_p"] = overall["short_p"] - overall["over_p"]
'''
ST_OVERALL_NEW = '''                   over_p=sum(S["totals"]["over_p"] for S in sections), unpriced=sum(S["totals"]["unpriced"] for S in sections),
                   neg_lines=sum(S["totals"]["neg_lines"] for S in sections))                                   # S432 (3.4)
    overall["net_p"] = overall["short_p"] - overall["over_p"]
'''
ST_PDF_HEAD_OLD = '''    doc.line_text("ALL SECTIONS: %d lines - %d differ, %d matched - short %s - excess %s - net %s%s" % (
        O["lines"], O["differing"], O["matched"], PR._rs(O["short_p"]), PR._rs(O["over_p"]), PR._rs(O["net_p"]), (" - %d line(s) without a price" % O["unpriced"]) if O["unpriced"] else ""), 10, bold=True)
'''
ST_PDF_HEAD_NEW = '''    doc.line_text("ALL SECTIONS: %d lines - %d differ, %d matched - short %s - excess %s - net %s%s%s" % (
        O["lines"], O["differing"], O["matched"], PR._rs(O["short_p"]), PR._rs(O["over_p"]), PR._rs(O["net_p"]), (" - %d line(s) without a price" % O["unpriced"]) if O["unpriced"] else "",
        (" - %d Marg-negative line(s): book corrections, no goods, no excess money" % O["neg_lines"]) if O.get("neg_lines") else ""), 10, bold=True)
'''
ST_PDF_KV_OLD = '''        if T["unpriced"]:
            doc.kv("Without a price", "%d: %s" % (T["unpriced"], ", ".join(T["unpriced_items"][:8]) + (" ..." if T["unpriced"] > 8 else "")), kw=170)
'''
ST_PDF_KV_NEW = '''        if T["unpriced"]:
            doc.kv("Without a price", "%d: %s" % (T["unpriced"], ", ".join(T["unpriced_items"][:8]) + (" ..." if T["unpriced"] > 8 else "")), kw=170)
        if T.get("neg_lines"):                                # S432 (3.4)
            doc.kv("Marg negative", "%d line%s -- book correction, no goods, not counted as excess: %s" % (T["neg_lines"], "" if T["neg_lines"] == 1 else "s", T["neg_text"]), kw=170)
'''
ST_XLSX_HEADS_OLD = '''    heads = ["Section", "Lines", "Differ", "Matched", "Short lines", "Short Rs", "Excess lines", "Excess Rs", "Net Rs", "Without a price", "Confirmed swaps"]
'''
ST_XLSX_HEADS_NEW = '''    heads = ["Section", "Lines", "Differ", "Matched", "Short lines", "Short Rs", "Excess lines", "Excess Rs", "Net Rs", "Without a price", "Confirmed swaps", "Marg negative (book corrections)"]   # S432
'''
ST_XLSX_VALS_OLD = '''        vals = [sec["title"], T["lines"], T["differing"], T["matched"], T["short_lines"], T["short_p"] / 100.0, T["over_lines"], T["over_p"] / 100.0, T["net_p"] / 100.0, T["unpriced"], T.get("swaps", 0)]
'''
ST_XLSX_VALS_NEW = '''        vals = [sec["title"], T["lines"], T["differing"], T["matched"], T["short_lines"], T["short_p"] / 100.0, T["over_lines"], T["over_p"] / 100.0, T["net_p"] / 100.0, T["unpriced"], T.get("swaps", 0), T.get("neg_lines", 0)]
'''
ST_XLSX_W_OLD = '''    tot.widths = {0: 34, 1: 8, 2: 8, 3: 9, 4: 11, 5: 13, 6: 12, 7: 13, 8: 12, 9: 14, 10: 14}
'''
ST_XLSX_W_NEW = '''    tot.widths = {0: 34, 1: 8, 2: 8, 3: 9, 4: 11, 5: 13, 6: 12, 7: 13, 8: 12, 9: 14, 10: 14, 11: 16}
'''
ST_XLSX_ROW_OLD = '''                    l["price_src"] or ("" if not (l["short"] or l["over"]) else "no price"), (l["short_p"] / 100.0) if l["short"] and l["price_p"] else "", (l["over_p"] / 100.0) if l["over"] and l["price_p"] else "",
                    l["became"], l["voucher"], "matched" if not (l["short"] or l["over"]) else ""]
'''
ST_XLSX_ROW_NEW = '''                    l["price_src"] or ("" if not (l["short"] or l["over"] or l.get("neg_marg")) else "no price"), (l["short_p"] / 100.0) if l["short"] and l["price_p"] else "", (l["over_p"] / 100.0) if l["over"] and l["price_p"] else "",
                    l["became"], l["voucher"], ("Marg negative" if l.get("neg_marg") else ("matched" if not (l["short"] or l["over"]) else ""))]   # S432
'''
ST_VERSION_OLD = '''VERSION = "1.0"
KIT = "S431_COUNT_STATEMENT"
'''
ST_VERSION_NEW = '''VERSION = "1.1"
KIT = "S432_DESK_GROUP_FLOW"                                   # v1.0 was S431_COUNT_STATEMENT
# v1.1 (S432, 3.4, 28-Sep-2026): a NEGATIVE Marg balance (PRIME CAST 4"/5", BELL CAST 5, ALCOXIB 120 ...) is a book correction, no
# goods -- tagged, its quantity to correct shown, EXCLUDED from the section's excess money and counted in its own line under the
# section totals; the Marg column carries the minus (qty_words v1.1).
'''


def build_statement(s):
    s = rep(s, ST_VERSION_OLD, ST_VERSION_NEW, "the statement's version")
    s = rep(s, ST_LINE_OLD, ST_LINE_NEW, "the Marg-negative line")
    s = rep(s, ST_TOT_OLD, ST_TOT_NEW, "the section totals' Marg-negative line")
    s = rep(s, ST_OVERALL_OLD, ST_OVERALL_NEW, "the overall totals")
    s = rep(s, ST_PDF_HEAD_OLD, ST_PDF_HEAD_NEW, "the PDF's head line")
    s = rep(s, ST_PDF_KV_OLD, ST_PDF_KV_NEW, "the PDF's section kv")
    s = rep(s, ST_XLSX_HEADS_OLD, ST_XLSX_HEADS_NEW, "the XLSX totals heads")
    s = rep(s, ST_XLSX_VALS_OLD, ST_XLSX_VALS_NEW, "the XLSX totals vals")
    s = rep(s, ST_XLSX_W_OLD, ST_XLSX_W_NEW, "the XLSX totals widths")
    s = rep(s, ST_XLSX_ROW_OLD, ST_XLSX_ROW_NEW, "the XLSX line row")
    return s


# ---------------------------------------------------------------- stock_statement.html
HT_TOT_OLD = '''    +'<div><div class="k">Net</div><div class="v">'+rs(T.net_p)+'</div><div class="c">'+(T.unpriced?'<span class="err">'+T.unpriced+' without a price</span>':'every differing line priced')+'</div></div>'+(extra||'')+'</div>';
'''
HT_TOT_NEW = '''    +'<div><div class="k">Net</div><div class="v">'+rs(T.net_p)+'</div><div class="c">'+(T.unpriced?'<span class="err">'+T.unpriced+' without a price</span>':'every differing line priced')+'</div></div>'
    +(T.neg_lines?'<div><div class="k">Marg negative</div><div class="v">'+T.neg_lines+'</div><div class="c">book correction, no goods — not excess</div></div>':'')+(extra||'')+'</div>';   /* S432 (3.4) */
'''
HT_ROW_OLD = '''    +'<td class="n">'+esc(l.marg_text)+'</td><td class="n">'+esc(l.counted_text)+'</td><td class="n short">'+esc(l.short_text||'')+'</td><td class="n over">'+esc(l.over_text||'')+'</td>'
'''
HT_ROW_NEW = '''    +'<td class="n">'+esc(l.marg_text)+'</td><td class="n">'+esc(l.counted_text)+'</td><td class="n short">'+esc(l.short_text||'')+'</td><td class="n over">'+(l.neg_marg?'<span class="tag" title="Marg negative — book correction, no goods">'+esc(l.correct_text)+' to correct</span>':esc(l.over_text||''))+'</td>'
'''
HT_SEC_OLD = '''  if(T.unpriced) h+='<div class="sub err">No price on record: '+esc(T.unpriced_items.join(", "))+'</div>';
'''
HT_SEC_NEW = '''  if(T.unpriced) h+='<div class="sub err">No price on record: '+esc(T.unpriced_items.join(", "))+'</div>';
  if(T.neg_lines) h+='<div class="sub"><b>Marg negative</b> — book correction, no goods, not counted as excess: '+lines(T.neg_lines)+' — '+esc(T.neg_text)+'</div>';   /* S432 (3.4) */
'''


def build_statement_html(s):
    s = rep(s, HT_TOT_OLD, HT_TOT_NEW, "the totals' Marg-negative cell")
    s = rep(s, HT_ROW_OLD, HT_ROW_NEW, "the row's Excess cell")
    s = rep(s, HT_SEC_OLD, HT_SEC_NEW, "the section's Marg-negative line")
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    src = {name: load(os.path.join(a.finance, name), name) for name in FROM}
    out = {"stock_app.py": build_stock_app(src["stock_app.py"]), "stock_statement.py": build_statement(src["stock_statement.py"]),
           "stock_statement.html": build_statement_html(src["stock_statement.html"])}
    os.makedirs(a.out, exist_ok=True)
    for name, text in out.items():
        b = text.encode("utf-8")
        with open(os.path.join(a.out, name), "wb") as fh:
            fh.write(b)
        print("%s  %s" % (md5(b), name))


if __name__ == "__main__":
    main()
