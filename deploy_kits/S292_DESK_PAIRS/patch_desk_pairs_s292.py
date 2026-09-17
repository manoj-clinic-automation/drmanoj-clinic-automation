#!/usr/bin/env python3
"""S292_DESK_PAIRS -- the "over" card stops being a wall of text.

The owner, 17-Sep-2026, on the desk at count #1: the card "3 items over" carried a
single paragraph naming every same-salt pair in the whole count -- twenty-odd pairs
run together, most of them nothing to do with the three items on the card. He asked
for the formatting to be fixed. Four anchored edits in the page's own script and one
stylesheet rule; no server code, no restart:

  1. the "over" card's sentence loses the pair dump (pairText() is no longer glued in);
  2. every lane card gets a PAIRS block under its sentence: one line per item ON THE
     CARD, naming its own same-salt partner (or "no same-salt pair"), and a
     "Show all N same-salt pairs" toggle for the rest, one pair per line;
  3. an item card (a real shelf loss) shows its own partner under the facts --
     "same salt ETORICOXIB 90: PARI CR 12.5 is over 18 strips 3 tabs -- a billing swap
     is the usual answer";
  4. one stylesheet rule for the block.

Usage (the installer does this):
    python3 -B patch_desk_pairs_s292.py --file /root/finance/stock_desk.html --from <md5>
"""
from __future__ import print_function
import argparse
import hashlib
import io
import shutil
import sys

EDITS = [
    # 1 -- the over card: no pair dump in the sentence
    ('or a purchase was never entered. "+pairText()+"Marking them explained keeps them out of the loss totals; Amir sees them on the report.",',
     'or a purchase was never entered. Each item\'s own partner is listed below. Marking them explained keeps them out of the loss totals; Amir sees them on the report.",'),
    # 2 -- lane cards: the pairs block under the sentence
    ('''      +'<div class="why">'+esc(c.why)+'</div>'
      +'<div class="btns">'+c.btns.map(b=>'<button class="b '+b[3]+'" data-act="'+b[0]+'" data-all="1">\'''',
     '''      +'<div class="why">'+esc(c.why)+'</div>'+pairBlock(c.xs)
      +'<div class="btns">'+c.btns.map(b=>'<button class="b '+b[3]+'" data-act="'+b[0]+'" data-all="1">\''''),
    # 3 -- item cards: the item's own partner under the facts
    ('''+(x.answer?' · staff say: '+esc(x.answer.label)+(x.answer.note?' — '+esc(x.answer.note):''):'')+'</div>'
      +'<div class="btns">'+c.btns.map(b=>'<button class="b '+b[3]+'" data-act="'+b[0]+'" data-item="'+esc(x.item)+'">\'''',
     '''+(x.answer?' · staff say: '+esc(x.answer.label)+(x.answer.note?' — '+esc(x.answer.note):''):'')+'</div>'+pairLine(x.item)
      +'<div class="btns">'+c.btns.map(b=>'<button class="b '+b[3]+'" data-act="'+b[0]+'" data-item="'+esc(x.item)+'">\''''),
    # 4 -- the stylesheet rule, beside .facts
    ('.card .facts{font-size:13.5px;color:var(--ink-2);margin:6px 0;padding-left:10px;border-left:3px solid var(--line)}',
     '.card .facts{font-size:13.5px;color:var(--ink-2);margin:6px 0;padding-left:10px;border-left:3px solid var(--line)}\n'
     '.pairs{margin:8px 0 4px;font-size:13.5px}.pairs .ph{font-weight:700;color:var(--muted);font-size:11px;letter-spacing:.06em;text-transform:uppercase;margin-bottom:4px}'
     '.pairs .pr{padding:5px 0 5px 10px;border-left:3px solid var(--line);margin:3px 0;color:var(--ink-2)}.pairs .pr b{color:var(--ink)}.pairs .pr .salt{display:block;font-size:11.5px;color:var(--muted)}'
     '.pairs button.more{font:inherit;font-size:12.5px;margin-top:4px;padding:4px 10px;border-radius:999px;border:1px solid var(--line);background:var(--surface);color:var(--muted);cursor:pointer}'
     '.pairs .all{margin-top:6px}.pairs .all[hidden]{display:none}'),
]

# the two helpers, placed beside pairText() (which stays for anyone else who calls it)
HELPERS_ANCHOR = 'function pairText(){'
HELPERS = ('function pairFor(item){ const P=(D&&D.pairs)||[]; for(const p of P){ '
           'if((p.over||[]).some(o=>o.item===item)) return {p:p,side:"over"}; if((p.short||[]).some(o=>o.item===item)) return {p:p,side:"short"}; } return null; }\n'
           'function pairSide(list){ return (list||[]).map(o=>"<b>"+esc(o.item)+"</b> "+esc(units(o.diff,o.pack))+(o.diff>0?" over":"")).join(", "); }\n'
           'function pairLine(item){ const f=pairFor(item); if(!f) return ""; const other=f.side==="over"?f.p.short:f.p.over; if(!other||!other.length) return ""; '
           'return \'<div class="pairs"><div class="pr">Same salt <span class="salt">\'+esc(f.p.salt)+\'</span>\'+pairSide(other)+(f.side==="short"?" — a billing swap is the usual answer, not a loss":" — the other half of this shortage")+\'</div></div>\'; }\n'
           'function pairBlock(xs){ const P=(D&&D.pairs)||[]; const rows=(xs||[]).map(x=>{ const f=pairFor(x.item); '
           'return \'<div class="pr"><b>\'+esc(x.item)+\'</b> \'+esc(units(x.diff,x.pack))+(x.diff>0?" over":"")+(f?\' — against \'+pairSide(f.side==="over"?f.p.short:f.p.over)+\'<span class="salt">same salt \'+esc(f.p.salt)+\'</span>\':\' — no same-salt pair found\')+\'</div>\'; }).join(""); '
           'const all=P.map(p=>\'<div class="pr">\'+pairSide(p.over)+\' against \'+pairSide(p.short)+\'<span class="salt">\'+esc(p.salt)+\'</span></div>\').join(""); '
           'return \'<div class="pairs"><div class="ph">Each item and its partner</div>\'+rows+(P.length?\'<button type="button" class="more" data-more="1">Show all \'+P.length+\' same-salt pair\'+(P.length===1?"":"s")+\' in this count</button><div class="all" hidden>\'+all+\'</div>\':"")+\'</div>\'; }\n'
           'document.addEventListener("click",e=>{ const m=e.target.closest("button[data-more]"); if(!m) return; const a=m.nextElementSibling; a.hidden=!a.hidden; m.textContent=(a.hidden?"Show":"Hide")+m.textContent.slice(4); });\n')


def md5(b):
    return hashlib.md5(b).hexdigest()


def apply(text):
    for old, new in EDITS:
        if text.count(old) != 1:
            raise SystemExit("REFUSING: anchor not found exactly once: %r" % old[:70])
        text = text.replace(old, new)
    if text.count(HELPERS_ANCHOR) != 1:
        raise SystemExit("REFUSING: helper anchor not found exactly once")
    text = text.replace(HELPERS_ANCHOR, HELPERS + HELPERS_ANCHOR)
    return text


def already(text):
    return "function pairBlock(" in text


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--from", dest="from_md5", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    raw = io.open(a.file, "rb").read()
    cur = md5(raw)
    text = raw.decode("utf-8")
    if already(text):
        print("ALREADY PATCHED: %s is %s" % (a.file, cur))
        return 0
    if a.from_md5 and cur != a.from_md5.lower():
        sys.exit("REFUSING: %s is %s, you said %s" % (a.file, cur, a.from_md5))
    new = apply(text).encode("utf-8")
    if a.dry_run:
        print("would write %s -> %s  (+%d bytes)" % (cur, md5(new), len(new) - len(raw)))
        return 0
    bak = "%s.bak_S292_%s" % (a.file, cur[:8])
    shutil.copy2(a.file, bak)
    with io.open(a.file, "wb") as fh:
        fh.write(new)
    back = md5(io.open(a.file, "rb").read())
    print("patched %s : %s -> %s  (backup %s)" % (a.file, cur, back, bak))
    return 0 if back == md5(new) else 4


if __name__ == "__main__":
    sys.exit(main())
