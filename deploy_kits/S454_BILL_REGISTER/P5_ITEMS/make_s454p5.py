#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s454p5.py -- kit S454_BILL_REGISTER, part 5 (S454 section 11: the items). CLAUDE.md rule 2: every live file built from its live bytes
(every anchor exactly once, FROM -> TO pinned); item_check.py is new.

  purchase_app.py  11.2  the Sarvam check judges a scan's item name by the supplier's learnt names first (_s446_compare_one); after each
                         compare the learner runs (item_check.learn), and when it learnt a name the rows of that supplier's bills are compared
                         again (sarvam_compare)
                   11.1  the owner's items page: GET /finance/purchase/page/items?month=YYYY-MM (the owner only); one link to it on the
                         Sarvam page

    make_s454p5.py --finance /root/finance --kit DIR --out DIR
"""
import argparse
import hashlib
import os

FROM = {"purchase_app.py": "61e6d26abe52293883e37cc61b459da5"}
NEWF = ("item_check.py",)

PA = [('''        nm = _s446_name_norm(it.get("item_name"))
        best, score = None, 0.0
        for x in ml:''',
       '''        nm = _s446_name_norm(it.get("item_name"))
        best, score = _s454_learnt_line(con, bill, nm, ml)            # S454 P5 (11.2): the supplier's learnt name first
        for x in ([] if best is not None else ml):'''),
      ('''    return _page("Sarvam against Marg — %s" % _month_name(month), body)''',
       '''    body += ('<div class="muted" id="s454items"><a href="%s/page/items?month=%s">Items check — do the bills add up line by line? (%s)</a></div>'   # S454 P5
             % (request.script_root + _url_prefix, month, _esc(_month_name(month))))
    return _page("Sarvam against Marg — %s" % _month_name(month), body)''')]

PA_APPEND = '''

# ==========================================================================================================================================
# S454_BILL_REGISTER part 5 (03-Oct-2026, S454 11): the items. item_check.py holds the rules; here they meet the Sarvam check and the owner.
#   * the Sarvam check judges a scan's item name by the supplier's learnt names first (_s454_learnt_line, in _s446_compare_one)
#   * sarvam_compare: after each compare the learner runs over the VERIFIED links; a name newly learnt sends that supplier's rows to be
#     compared again, so the Sarvam page's item figure counts by the learnt names. Nothing here changes stock, an order or a bill.
#   * GET /page/items?month=YYYY-MM -- the items check (11.1), the owner only, English, phone width.
# ==========================================================================================================================================
def _s454_ic():
    import item_check                                         # noqa: PLC0415 -- beside this file
    return item_check


def _s454_learnt_line(con, bill, nm, ml):
    try:
        return _s454_ic().learnt_line(con, bill, nm, ml)
    except Exception:                                          # noqa: BLE001 -- the check never fails for it: the old matching stands
        return None, 0.0


_s454p5_compare_before = sarvam_compare


def sarvam_compare(con):                                          # noqa: F811
    """S446's compare, then the learner (S454 11.2); a supplier with a name newly learnt has its rows compared again."""
    n = _s454p5_compare_before(con)
    try:
        new = _s454_ic().learn(con)
    except Exception:                                          # noqa: BLE001
        new = []
    if new:
        sups = sorted({x["supplier_norm"] for x in new})
        con.execute("DELETE FROM purchase_sarvam_check WHERE bill_id IN (SELECT id FROM purchase_bill WHERE supplier_norm IN (%s))" % ",".join("?" * len(sups)), sups)
        con.commit()
        n += _s454p5_compare_before(con)
    return n


def _s454_items_body(con, month, prefix):
    IC = _s454_ic()
    r = IC.items_check(con, month)
    months = [m[0] for m in con.execute("SELECT DISTINCT COALESCE(month, substr(bill_date,1,7)) m FROM purchase_bill WHERE m IS NOT NULL ORDER BY m DESC LIMIT 4")]
    nav = " · ".join(('<b>%s</b>' % _esc(_month_name(m))) if m == month else '<a href="%s/page/items?month=%s">%s</a>' % (prefix, m, _esc(_month_name(m)))
                     for m in months)
    withl = r["n"] - r["nolines"]
    head = ("%s: %d of %d bill%s add up (the lines' value comes to the bill within %s); %d do%s not." % (
        _month_name(month), r["adds"], withl, "" if withl == 1 else "s", _r(r["noise_p"]), r["differs"], "es" if r["differs"] == 1 else ""))
    if r["nolines"]:
        head += " %d bill%s ha%s no lines on the server." % (r["nolines"], "" if r["nolines"] == 1 else "s", "s" if r["nolines"] == 1 else "ve")
    rows = []
    for b in r["rows"]:
        ls = "".join("<tr><td>%s</td><td>%s%s</td><td>%s</td><td>%s%%</td><td>%s%%</td><td>%s</td><td>%s</td></tr>" % (
            _esc(l["item"]), _esc("%g" % float(l["qty"] or 0)), (" + %g free" % float(l["free"])) if l.get("free") else "",
            _esc("%.2f" % (float(l["rate_p"] or 0) / 100.0)), _esc("%g" % float(l["disc"] or 0)), _esc("%g" % float(l["tax"] or 0)),
            _r(l["value_p"]), _r(l["marg_net_p"]) if l.get("marg_net_p") is not None else "-") for l in b["lines"])
        rows.append('<div class="card" data-bill="%d"><div><b>%s</b> · bill %s · %s</div><div>Bill %s · its lines come to %s · <b>%s%s</b></div>'
                    '<details><summary>%d line%s</summary><div class="scroll"><table><tr><th>item</th><th>qty</th><th>rate</th><th>disc.</th><th>tax</th>'
                    '<th>value</th><th>Marg\\'s net</th></tr>%s</table></div></details></div>'
                    % (b["id"], _esc(b["supplier"]), _esc(b["bill_no"]), _esc(b["date"]), _r(b["amount_p"]), _r(b["value_p"]),
                       "+" if b["diff_p"] > 0 else "-", _r(abs(b["diff_p"])), len(b["lines"]), "" if len(b["lines"]) == 1 else "s", ls))
    learnt = IC.learnt(con)
    ln = "".join("<li>%s: “%s” = %s</li>" % (_esc(x["supplier_norm"]), _esc(x["scan_name"]), _esc(x["marg_item"])) for x in learnt)
    return ('<h1>Items check — %s</h1><div class="muted">%s</div><div class="card" id="s454itemshead"><b>%s</b><div class="muted">Each line\\'s value is '
            'quantity × rate, less the discount, plus the tax, as Marg holds them; free goods are not charged. "Marg\\'s net" is Marg\\'s own figure '
            'for the line: where it differs from the value, something reached the bill that the line\\'s columns do not show.</div></div>%s'
            '<div class="card" id="s454learnt"><b>Item names learnt from the suppliers\\' bills: %d</b><div class="muted">Learnt from bills whose scan '
            'agrees with Marg (verified), line by line where the quantity and the rate agree. They change no stock, order or bill; the Sarvam '
            'page judges a name by them first.</div><ul>%s</ul></div>'
            % (_esc(_month_name(month)), nav, _esc(head), "".join(rows) or '<div class="card">Every bill of the month adds up.</div>', len(learnt), ln))


@bp.route("/page/items")
def page_s454_items():
    u, err = _person("checker")
    if err:
        return err
    if not _is_doctor(u):                                      # the owner's page (S454 11.1)
        return _refuse("This page is for the doctor only.")
    con = _db()
    _ensure(con)
    newest =con.execute("SELECT MAX(COALESCE(month, substr(bill_date,1,7))) FROM purchase_bill").fetchone()[0] or dt.date.today().strftime("%Y-%m")
    month = str(request.args.get("month") or newest)[:7]
    if not re.match(r"^\\d{4}-\\d{2}$", month):
        return "bad month", 400
    return _page("Items check — %s" % _month_name(month), _s454_items_body(con, month, request.script_root + _url_prefix))
# ---- S454 part 5 end -------------------------------------------------------------------------------------------------------------------
'''

EDITS = {"purchase_app.py": PA}
APPEND = {"purchase_app.py": PA_APPEND}
GUARD = "\nif __name__ == \"__main__\":"


def place_block(txt, block):
    """The block goes ABOVE the file's `if __name__ == "__main__":` guard (purchase_app.py rematch runs as a script -- part 1D's lesson)."""
    c = txt.count(GUARD)
    if c > 1:
        raise SystemExit("STOP: the __main__ guard occurs %d times -- nothing built" % c)
    if c == 1:
        i = txt.index(GUARD)
        return txt[:i].rstrip("\n") + "\n" + block.rstrip("\n") + "\n\n" + txt[i:]
    return txt.rstrip("\n") + "\n" + block


def md5b(b):
    return hashlib.md5(b).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for f in sorted(FROM):
        raw = open(os.path.join(a.finance, f), "rb").read()
        m = md5b(raw)
        if m != FROM[f]:
            raise SystemExit("STOP: %s is %s, not its FROM pin %s -- nothing built" % (f, m, FROM[f]))
        txt = raw.decode("utf-8")
        for old, new in EDITS.get(f, []):
            c = txt.count(old)
            if c != 1:
                raise SystemExit("STOP: an anchor occurs %d times in %s -- nothing built: %r" % (c, f, old[:90]))
            txt = txt.replace(old, new, 1)
        if f in APPEND:
            txt = place_block(txt, APPEND[f])
        out = txt.encode("utf-8")
        open(os.path.join(a.out, f), "wb").write(out)
        print("built %-18s %s -> %s  (%d edits%s)" % (f, m[:8], md5b(out), len(EDITS.get(f, [])), " + 1 block" if f in APPEND else ""))
    for f in NEWF:
        if os.path.exists(os.path.join(a.finance, f)):
            raise SystemExit("STOP: %s exists already on the box -- nothing built" % f)
        raw = open(os.path.join(a.kit, f), "rb").read()
        open(os.path.join(a.out, f), "wb").write(raw)
        print("new   %-18s %s" % (f, md5b(raw)))


if __name__ == "__main__":
    main()
