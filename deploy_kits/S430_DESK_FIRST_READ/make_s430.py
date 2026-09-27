#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s430.py -- builds the patched live files of kit S430_DESK_FIRST_READ from the LIVE bytes by anchored edits. Every anchor must
occur exactly once and every source must be at its FROM pin, or the build stops with nothing written. Nothing is re-typed.
(loss_piles.py v2.1 and stock_watch.py v1.1 are whole-file replacements shipped in the kit.)

  stock_loss.html    the -> pile menu's fifth destination 'Owner's use'; the Consumption pile shows its two groups; the Close-the-count
                     button repeated at the top under the totals; one line on each of the three piles' headers
  stock_amir.html    a voucher round made of owner's-use lines is labelled 'owner's use'
  order_rules.py     the four 'units' hints (keep-in-stock, max on shelf, on order x2) read in strips / pcs through qty_words

Usage: make_s430.py --finance /root/finance --out DIR
"""
import argparse
import hashlib
import os
import sys

FROM = {
    "stock_loss.html": "29809ba1e3ce415fc43f5df614f7ea0e",
    "stock_amir.html": "e5e229270de7a71a624505bfd0ca11b7",
    "order_rules.py": "b17226d4cc10d7cf9fef8a75465ac76b",
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


# ---------------------------------------------------------------- stock_loss.html
def build_loss(s):
    s = rep(s, '''const PILES=[["with_me","With me / back in store"],["writeoff","Write off"],["bigloss","Big losses"],["consume","Consumption"]];
''', '''const PILES=[["with_me","With me / back in store"],["writeoff","Write off"],["bigloss","Big losses"],["consume","Consumption (clinic)"],["owner_use","Owner's use — taken for home, unbilled"]];   // S430: the fifth destination
''', "the move targets")
    s = rep(s, '''  PILES.forEach(p=>{ if(p[0]!==l.pile) h+='<option value="'+p[0]+'">'+esc(p[1])+'</option>'; });
''', '''  const cur=(l.moved&&l.moved.target)||(l.group==="owner_use"?"owner_use":l.pile);   // S430
  PILES.forEach(p=>{ if(p[0]!==cur) h+='<option value="'+p[0]+'">'+esc(p[1])+'</option>'; });
''', "the current target hidden")
    s = rep(s, '''cell("Consumption",T.consume)''', '''cell("Consumption & owner's use",T.consume)''', "the tally cell")
    s = rep(s, '''  document.getElementById("tally").innerHTML=h;
''', '''  document.getElementById("tally").innerHTML=h+(D.close?'<div class="card" style="margin:6px 0 0;padding:8px 12px">'+closeBtn()+'</div>':'');   // S430 (2.4): the one Close button, also at the top
''', "the top Close button")
    s = rep(s, '''    +'<div class="sum">'+lines(P.n)+' · '+rs(P.mrp_p)+' at MRP · '+rs(P.cost_p)+' at cost'+(P.unpriced?' · '+P.unpriced+' without a price':'')+'</div>';
''', '''    +'<div class="sum">'+lines(P.n)+' · '+rs(P.mrp_p)+' at MRP · '+rs(P.cost_p)+' at cost'+(P.unpriced?' · '+P.unpriced+' without a price':'')+'</div>'
    +(k!=="with_me"?'<div class="lead" style="color:var(--accent);font-weight:600">Written off by <b>Close the count</b> — one tap for all three piles, at the top and the foot.</div>':'');   // S430 (2.4)
''', "the piles' header line")
    s = rep(s, '''  } else {
    h+='<p class="lead">Only the items on your consumption list ('+(R.consume_items.length?esc(R.consume_items.slice(0,4).join(", "))+(R.consume_items.length>4?' …':''):'empty')+') — used in the clinic, never billed. Written off as clinic consumption by the close. Add or take off names in Settings below.</p>'+m;
    h+=listHtml(k,P.lines);
  }
''', '''  } else {
    h+='<p class="lead"><b>Clinic consumption</b>: only the items on your consumption list ('+(R.consume_items.length?esc(R.consume_items.slice(0,4).join(", "))+(R.consume_items.length>4?' …':''):'empty')+') — used in the clinic, never billed. <b>Owner\\'s use</b>: lines you moved here — taken for home, unbilled; a recorded non-loss, never leakage, never on the staff block. Both written off by the close, each in its own group.</p>'+m;
    const G2=P.groups||{};
    D.groups.forEach(g=>{                                        // S430: the two groups of this pile
      const ls=P.lines.filter(l=>l.group===g.key); if(!ls.length) return;
      const t=G2[g.key]||{n:ls.length,mrp_p:ls.reduce((a,l)=>a+(l.mrp_p||0),0)};
      h+='<div class="grp"><span>'+esc(g.title)+'</span><span>'+lines(t.n)+' · '+rs(t.mrp_p)+'</span></div><div class="lead">'+esc(dash(g.blurb))+'</div>'+listHtml(k+"_"+g.key,ls);
    });
    if(!P.lines.length) h+='<div class="none">Nothing here.</div>';
  }
''', "the Consumption pile's two groups")
    s = rep(s, '''  const go=(ARM&&ARM.n)?'<button class="b warn" id="clyes">Yes, close the count — '+lines(ARM.n)+'<small id="clcd">'+rs(ARM.mrp_p)+' at MRP — this button goes away in '+ARM.left+' s</small></button>'
    :'<button class="b main" id="clarm"'+(C.n?'':' disabled')+'>Close the count ('+lines(C.n)+')<small>'+rs(C.mrp_p)+' at MRP — you confirm on the next tap</small></button>';
''', '''  const go=closeBtn();
''', "the foot button through closeBtn")
    s = rep(s, '''function soldAfterHtml(){
''', '''function closeBtn(){                                            // S430 (2.4): ONE button, drawn at the top and at the foot; one arm, one confirm
  const C=D.close||{n:0,mrp_p:0};
  return (ARM&&ARM.n)?'<button class="b warn" data-close-yes="1">Yes, close the count — '+lines(ARM.n)+'<small class="clcd">'+rs(ARM.mrp_p)+' at MRP — this button goes away in '+ARM.left+' s</small></button>'
    :'<button class="b main" data-close-arm="1"'+(C.n?'':' disabled')+'>Close the count ('+lines(C.n)+')<small>'+rs(C.mrp_p)+' at MRP · every line in Write off, Big losses and Consumption &amp; owner\\'s use — you confirm on the next tap</small></button>';
}
function soldAfterHtml(){
''', "closeBtn")
    s = rep(s, '''  if(t.closest("#clarm")){ BUSY=true;
''', '''  if(t.closest("[data-close-arm]")){ BUSY=true;                // S430: the top and the foot button share one arm
''', "the arm handler")
    s = rep(s, '''const cd=document.getElementById("clcd"); if(cd) cd.textContent=rs(ARM.mrp_p)+" at MRP — this button goes away in "+ARM.left+" s"; },1000);
''', '''document.querySelectorAll(".clcd").forEach(cd=>{ cd.textContent=rs(ARM.mrp_p)+" at MRP — this button goes away in "+ARM.left+" s"; }); },1000);
''', "the countdown on both buttons")
    s = rep(s, '''  if(t.closest("#clyes")&&ARM){ BUSY=true; const tok=ARM.token; disarm();
''', '''  if(t.closest("[data-close-yes]")&&ARM){ BUSY=true; const tok=ARM.token; disarm();
''', "the confirm handler")
    s = rep(s, '''    } else say("close",j);
    render(); return; }
''', '''    } else say("close",j);
    render(); tally(); return; }
''', "re-draw the top button when armed")
    return s


# ---------------------------------------------------------------- stock_amir.html
def build_amir(s):
    s = rep(s, '''(r.batches.every(b=>(b.sections||[]).length===1&&b.sections[0]==="Orthotics")?' — orthotics':'')''',
            '''(r.batches.every(b=>(b.sections||[]).length===1&&b.sections[0]==="Orthotics")?' — orthotics':'')+(r.batches.length&&r.batches.every(b=>(b.lines||[]).length&&(b.lines||[]).every(l=>/Owner's use/.test(l.reason||"")))?' — owner\\'s use (taken for home, unbilled)':'')''',
            "the owner's-use round label")
    return s


# ---------------------------------------------------------------- order_rules.py
QW_BLOCK = '''HERE = os.path.dirname(os.path.abspath(__file__))

# --- S430_DESK_FIRST_READ (D637 / F-650): a quantity in the item's own words -- strips / pcs by its packing, never 'units' ----
try:
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import qty_words as _qty                                   # noqa: PLC0415 -- beside this file (S427)
    QTY_WORDS_OK = True
except Exception:                                              # pragma: no cover
    _qty = None
    QTY_WORDS_OK = False


def _qw(units, s):
    """'12 strips + 4 tabs' / '3 pcs' from the snapshot row's packing and pack size; the bare figure when qty_words is away."""
    if QTY_WORDS_OK:
        return _qty.words(units, packing=(s or {}).get("packing"), pack=(s or {}).get("pack_size"))
    return "%d" % int(units or 0)
# --- S430 end -----------------------------------------------------------------------------------------------------------------
'''


def build_rules(s):
    s = rep(s, "HERE = os.path.dirname(os.path.abspath(__file__))\n", QW_BLOCK, "the qty_words door")
    s = rep(s, '''                extra.append("keep-in-stock %d units (your rule)" % int(ir["value"]))
''', '''                extra.append("keep-in-stock %s (your rule)" % _qw(int(ir["value"]), s))   # S430: strips / pcs, never 'units'
''', "keep-in-stock hint")
    s = rep(s, '''                extra.append("max on shelf %d units (your rule) -- cut from %d" % (int(ir["value"]), line["order_strips"]))
''', '''                extra.append("max on shelf %s (your rule) -- cut from %s" % (_qw(int(ir["value"]), s), _qw(line["order_strips"] * int(s["pack_size"] or 1), s)))   # S430
''', "max on shelf hint")
    s = rep(s, '''            extra.append("%d units on order #%d (sent %s), not yet received -- counted as stock" % (tr["on_way"]["units"], tr["on_way"]["order_id"], _dmy(tr["on_way"]["sent"])))
''', '''            extra.append("%s on order #%d (sent %s), not yet received -- counted as stock" % (_qw(tr["on_way"]["units"], s), tr["on_way"]["order_id"], _dmy(tr["on_way"]["sent"])))   # S430
''', "on order hint (the plan)")
    s = rep(s, '''            why.append("%d units on order #%d (sent %s) counted as stock" % (tr["on_way"]["units"], tr["on_way"]["order_id"], _dmy(tr["on_way"]["sent"])))
''', '''            why.append("%s on order #%d (sent %s) counted as stock" % (_qw(tr["on_way"]["units"], s), tr["on_way"]["order_id"], _dmy(tr["on_way"]["sent"])))   # S430
''', "on order hint (the interim)")
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    src = {name: load(os.path.join(a.finance, name), name) for name in FROM}
    out = {"stock_loss.html": build_loss(src["stock_loss.html"]), "stock_amir.html": build_amir(src["stock_amir.html"]),
           "order_rules.py": build_rules(src["order_rules.py"])}
    os.makedirs(a.out, exist_ok=True)
    for name, text in out.items():
        b = text.encode("utf-8")
        with open(os.path.join(a.out, name), "wb") as fh:
            fh.write(b)
        print("%s  %s" % (md5(b), name))


if __name__ == "__main__":
    main()
