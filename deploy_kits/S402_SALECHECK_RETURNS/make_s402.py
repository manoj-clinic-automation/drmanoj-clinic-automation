#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s402.py -- builds the two patched files of kit S402_SALECHECK_RETURNS from the LIVE bytes (S400 pins) by anchored
edits. Every anchor must occur exactly once and every source must be at its FROM pin, or nothing is written.

  sale_check.py     v1.0 -> v1.1: a return row is bill no · name · amount (positive, whole rupees) and nothing more;
                    the list card carries returns {count, total}
  sale_check.html   the day view: one collapsible block 'Sale return — N · ₹T' right after the Marg bills (0 does not
                    expand); the card: one line 'Sale return N · ₹T' when N > 0

Usage: make_s402.py --finance /root/finance --out DIR
"""
import hashlib
import os
import sys

FROM = {"sale_check.py": "81cccad3c48a894298b3694a7b3b5118", "sale_check.html": "4202d11baee4c9309a518e3aed8cf817"}


def md5(b):
    return hashlib.md5(b).hexdigest()


def load(path, name):
    raw = open(path, "rb").read()
    if md5(raw) != FROM[name]:
        sys.exit("REFUSED: %s is %s, not its FROM pin %s" % (path, md5(raw), FROM[name]))
    return raw.decode("utf-8")


def rep(s, old, new, what):
    n = s.count(old)
    if n != 1:
        sys.exit("REFUSED: anchor for %s found %d times (need exactly 1): %r" % (what, n, old[:70]))
    return s.replace(old, new)


def build_py(s):
    s = rep(s, '''#  sale_check.py  ·  v1.0  ·  kit S400_MEDICAL_SALE_CHECK  ·  Session 283 (Sanjeevni)  ·  D616
''', '''#  sale_check.py  ·  v1.1  ·  kit S402_SALECHECK_RETURNS  ·  Session 283 (Sanjeevni)  ·  D616
#  v1.1 (S402, the owner 25-Sep-2026): the day's sale returns at a glance -- count, total, and per return ONLY the bill no,
#  the name as the system shows it and the amount (positive, whole rupees); no medicine lines for returns. The list card
#  carries the count and total. Nothing else moves. v1.0 was kit S400_MEDICAL_SALE_CHECK.
''', "py header")
    s = rep(s, '''VERSION = "1.0"
''', '''VERSION = "1.1"
''', "py version")
    s = rep(s, '''    rets = [dict(bill=b["bill"], name=b.get("name") or "", amount=b["amount"],
                 items=[dict(item=i.get("item"), qty=i.get("qty") or "", amount=i.get("amount")) for i in (b.get("items") or [])])
            for b in (v["returns"]["list"] or [])]
''', '''    rets = [dict(bill=b["bill"], name=b.get("name") or "", amount=rs(abs(int(b.get("amount_p") or 0))))
            for b in (v["returns"]["list"] or [])]                  # S402: bill no · name · amount, nothing more
''', "py returns rows")
    s = rep(s, '''                        bills=v["sale"]["bills"], sale=v["sale"]["total"], chip=_chip(chk, issues),
''', '''                        bills=v["sale"]["bills"], sale=v["sale"]["total"], chip=_chip(chk, issues),
                        returns=dict(count=v["returns"]["count"], total=v["returns"]["total"]),   # S402
''', "py card returns")
    return s


def build_html(s):
    s = rep(s, '''     computed here. Never shown: drawer, pool, where the cash went, deposits, banks, months, other days. -->
''', '''     computed here. Never shown: drawer, pool, where the cash went, deposits, banks, months, other days.
     S402_SALECHECK_RETURNS (25-Sep-2026): the day's sale returns as one collapsible block -- 'Sale return — N · ₹T', tap ->
     bill no · name · amount per return, nothing more; the card carries 'Sale return N · ₹T' when N > 0. -->
''', "html header")
    s = rep(s, '''      '<div class="row"><span class="k">'+d.bills+' bill · Marg sale</span><span class="v">'+R(d.sale)+'</span></div>'+
''', '''      '<div class="row"><span class="k">'+d.bills+' bill · Marg sale</span><span class="v">'+R(d.sale)+'</span></div>'+
      ((d.returns&&d.returns.count)?'<div class="dline">Sale return '+d.returns.count+' · '+R(d.returns.total)+'</div>':"")+
''', "html card line")
    s = rep(s, '''    line("− Sale return",d.returns.total,d.returns.count?d.returns.count+" credit note":"koi nahi",d.returns.count?bills(d.returns.list):"")+
''', '''    retBlock(d.returns)+
''', "html day block")
    s = rep(s, '''function line(label,amount,sub,detail){
''', '''function retBlock(r){
 /* S402: 'Sale return — N · ₹T', collapsed; tap -> bill no · name · amount per return. 0 does not expand. */
 const n=(r&&r.count)||0;
 const head='<span class="k">− Sale return — '+n+(n?' <span class="muted">▸</span>':"")+'</span><span class="v">'+R(r&&r.total)+'</span>';
 if(!n)return '<div class="row">'+head+'</div>';
 return '<div class="row" onclick="var n=this.nextElementSibling;n.style.display=n.style.display===\\'none\\'?\\'\\':\\'none\\'" style="cursor:pointer">'+head+'</div>'+
   '<div style="display:none;padding:0 0 6px 8px"><table>'+r.list.map(x=>'<tr><td><b>'+esc(x.bill)+'</b></td><td class="muted">'+esc(x.name||"naam nahi")+'</td><td class="n">'+R(x.amount)+'</td></tr>').join("")+'</table></div>';
}
function line(label,amount,sub,detail){
''', "html retBlock")
    return s


def main(argv):
    a = dict(zip(argv[1::2], argv[2::2]))
    fin, out = a.get("--finance"), a.get("--out")
    if not (fin and out):
        print(__doc__)
        return 2
    os.makedirs(out, exist_ok=True)
    built = {"sale_check.py": build_py(load(os.path.join(fin, "sale_check.py"), "sale_check.py")),
             "sale_check.html": build_html(load(os.path.join(fin, "sale_check.html"), "sale_check.html"))}
    for name, text in built.items():
        data = text.encode("utf-8")
        open(os.path.join(out, name), "wb").write(data)
        print("%s  %s" % (md5(data), name))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
