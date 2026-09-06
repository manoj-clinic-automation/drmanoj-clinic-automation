#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S228 LOSS DESK -- builds the kit's four changed files from the S227_STAFF
pins, so the change is a readable transform and never a hand edit of 225 KB.

  stock_app.py     8eef6420 -> + the loss desk (schema, board, share, recovery, page)
  pad_receipt.py   a52751f4 -> + render_loss_share() (A4 PORTRAIT, frozen data only)
  stock_amir.html  56ed926f -> Darpan's LISTS leave Amir's board; his TYPING BOARD stays
  stock_desk.html  f044a5db -> one more link in the foot: the owner's loss desk
  stock_loss.html  NEW

Run it from inside the kit folder with the S227 files beside it; it refuses if a
source file is not the pinned one, and it writes nothing until every edit lands.
"""
import hashlib, io, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PINS = {"stock_app.py": "8eef6420", "pad_receipt.py": "a52751f4",
        "stock_amir.html": "56ed926f", "stock_desk.html": "f044a5db"}


def rd(n):
    with io.open(os.path.join(HERE, n), "r", encoding="utf-8") as fh:
        return fh.read()


def wr(n, s):
    with io.open(os.path.join(HERE, n), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(s)


def md5(n):
    with io.open(os.path.join(HERE, n), "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def once(hay, needle, what):
    n = hay.count(needle)
    if n != 1:
        raise SystemExit("REFUSED: %s -- the anchor appears %d times, not once." % (what, n))
    return True


for f, pin in PINS.items():
    if not os.path.exists(os.path.join(HERE, f)):
        raise SystemExit("REFUSED: %s is not beside this script." % f)
    if md5(f)[:8] != pin:
        raise SystemExit("REFUSED: %s is %s, not the pinned %s -- NOTHING CHANGED."
                         % (f, md5(f)[:8], pin))

app = rd("stock_app.py")
rec = rd("pad_receipt.py")
amir = rd("stock_amir.html")
desk = rd("stock_desk.html")
block_app = rd("_block_loss.py")
block_rec = rd("_block_receipt.py")

# ---------------------------------------------------------------- stock_app.py
# 1. the page constant, beside the others
A1 = [l for l in app.split("\n") if l.startswith("PAGE_AMIR = ")]
if len(A1) != 1:
    raise SystemExit("REFUSED: stock_app.py -- %d PAGE_AMIR lines, not one." % len(A1))
A1 = A1[0] + "\n"
once(app, A1, "stock_app.py PAGE_AMIR")
app = app.replace(A1, A1 + 'PAGE_LOSS = os.path.join(HERE, "stock_loss.html")      '
                          '# S228 LOSS DESK: the owner\'s own page\n')

# 2. the block itself, after the S227 report section closes
A2 = "# ---- end S227 FINDING REPORT ---------------------------------------------------\n"
once(app, A2, "stock_app.py end-of-report marker")
app = app.replace(A2, A2 + "\n\n" + block_app.rstrip("\n") + "\n")

# 3. the link, so the desk and the report can reach the owner's page
A3 = '                           amir_page="/finance/stock/page/amir?count=%d" % _root))\n'
once(app, A3, "stock_app.py links dict")
app = app.replace(A3, '                           amir_page="/finance/stock/page/amir?count=%d" % _root,\n'
                      '                           loss_page="/finance/stock/page/loss?count=%d" % _root))\n')

# ---------------------------------------------------------------- pad_receipt.py
A4 = '\n\nif __name__ == "__main__":                                   # a shape check, nothing more\n'
once(rec, A4, "pad_receipt.py __main__ guard")
rec = rec.replace(A4, "\n" + block_rec.rstrip("\n") + "\n" + A4)

# ---------------------------------------------------------------- stock_amir.html
# Darpan's LISTS move to the owner (D389). Amir keeps the TYPING BOARD -- his work
# does not grow, and the owner's does not become typing (F-339).
A5 = """  h+='<div class="card"><h2><span class="n">3</span>Darpan\\'s lists — in turns</h2><div class="hi">दर्पण की लिस्ट — एक बार में 10 आइटम, दाम नहीं</div>'
    +'<div class="lead">Ten items at a time — five with the largest gaps, five routine — quantities only, no rates. Print, hand over, mark returned when he brings it back, type his answers below, then cut the next. Orthotics are a separate list.</div>'
    +(T.length?T.map(trow).join(""):'<div class="empty">No list cut yet.</div>')
    +'<div style="margin-top:10px">'+(open("med").length?'':'<button class="b main" data-next="med">Cut the next medicines list ('+(d.pool.med||0)+' left)</button>')+(open("ortho").length?'':'<button class="b" data-next="ortho">Cut the next orthotics list ('+(d.pool.ortho||0)+' left)</button>')+'</div><div class="msg" id="tmsg"></div>'
    +'<h3 style="font-size:15px;margin:14px 0 4px">Type Darpan\\'s answers</h3><div class="hi">दर्पण के जवाब यहाँ टाइप करें — कारण नंबर और टिप्पणी</div>'
"""
A5NEW = """  h+='<div class="card"><h2><span class="n">3</span>Type Darpan\\'s answers</h2><div class="hi">दर्पण के जवाब यहाँ टाइप करें — कारण नंबर और टिप्पणी</div>'
    +'<div class="lead">The doctor gives Darpan the list and takes it back. When a list comes back, its items appear here — type the reason number and the note against each, and record them.</div>'
    +(T.length?T.map(trow).join(""):'<div class="empty">No list has been given yet.</div>')
"""
once(amir, A5, "stock_amir.html box 3")
amir = amir.replace(A5, A5NEW)

# the row loses its buttons -- Amir reads the state, the owner drives it
A6 = ("""  const trow=t=>'<div class="tr"><div><b>List '+t.no+' — '+(t.kind==="ortho"?"orthotics":"medicines")+'</b> · '+t.items.length+' items<div class="st">given '+esc(t.issued_text)+(t.returned_at?' · back '+esc(t.returned_text):' · <b>with Darpan</b>')+'</div></div><div><a class="b" href="'+esc(t.pdf)+'" target="_blank" rel="noopener">Print</a>'+(t.returned_at?'':'<button class="b main" data-ret="'+t.id+'">Darpan returned it</button>')+'</div></div>';\n""")
A6NEW = ("""  const trow=t=>'<div class="tr"><div><b>List '+t.no+' — '+(t.kind==="ortho"?"orthotics":"medicines")+'</b> · '+t.items.length+' items<div class="st">given '+esc(t.issued_text)+(t.returned_at?' · back '+esc(t.returned_text)+' — type its answers below':' · <b>with Darpan</b> — nothing to type yet')+'</div></div><div></div></div>';\n""")
once(amir, A6, "stock_amir.html tranche row")
amir = amir.replace(A6, A6NEW)

# the typing table is four columns on a 390px phone and was being sliced by the
# card edge (the S228 screen read). It scrolls sideways now; nothing else changes.
A8 = ".board td.sel{min-width:140px}\n"
once(amir, A8, "stock_amir.html board css")
amir = amir.replace(A8, A8 + ".boardwrap{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:0 -4px;padding:0 4px}\n"
                         ".boardwrap table.board{min-width:520px}\n")
A9 = """return '<div class="sub">List '+last.no+' ('+(last.kind==="ortho"?"orthotics":"medicines")+')</div><table class="board">"""
once(amir, A9, "stock_amir.html board open")
amir = amir.replace(A9, """return '<div class="sub">List '+last.no+' ('+(last.kind==="ortho"?"orthotics":"medicines")+')</div><div class="boardwrap"><table class="board">""")
A10 = """+'</table><button class="b main" id="saveans">Record these answers</button>"""
once(amir, A10, "stock_amir.html board close")
amir = amir.replace(A10, """+'</table></div><button class="b main" id="saveans">Record these answers</button>""")

# ---------------------------------------------------------------- stock_desk.html
A7 = ("""(D.links.amir_page?'<a href="'+esc(D.links.amir_page)+'"><b>Amir\\'s board</b> — Marg\\'s jobs, uploads, Darpan\\'s lists</a>':'')""")
A7NEW = ("""(D.links.loss_page?'<a href="'+esc(D.links.loss_page)+'"><b>Your loss desk</b> — mark the losses, share the sheet</a>':'')+(D.links.amir_page?'<a href="'+esc(D.links.amir_page)+'"><b>Amir\\'s board</b> — Marg\\'s jobs and uploads</a>':'')""")
once(desk, A7, "stock_desk.html foot")
desk = desk.replace(A7, A7NEW)

wr("stock_app.py", app)
wr("pad_receipt.py", rec)
wr("stock_amir.html", amir)
wr("stock_desk.html", desk)

sys.stdout.write("PATCHED\n")
for f in ("stock_app.py", "pad_receipt.py", "stock_amir.html", "stock_desk.html", "stock_loss.html"):
    sys.stdout.write("  %s  %s\n" % (md5(f)[:8], f))
