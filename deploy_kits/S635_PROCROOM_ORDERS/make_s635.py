#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s635.py -- S635_PROCROOM_ORDERS (D773 Kit 2): rebuilds sorting_desk.py's TO bytes from the pinned FROM bytes by exact,
counted edits, and places the kit's procroom.py (the whole file, its FROM pinned by the installer) beside it.

    python3 -B make_s635.py <FROM folder> <TO folder>

Each edit's anchor must occur exactly ONCE in the FROM file; the FROM md5 must equal the pin; the TO md5 is printed.

The owner: D773 (S342, 23-Oct-2026) -- his signed order scanned, the slip joined to it, the system fills and he corrects; the
month-end check of Yuvika's WhatsApp, his only. His "start", 20:55 IST 24-Oct-2026 (session 346).
"""
import hashlib
import os
import shutil
import sys

FROM_PIN = {"sorting_desk.py": "43658394d65a02affaf05a1ebfae3f26"}
HERE = os.path.dirname(os.path.abspath(__file__))

EDITS = {"sorting_desk.py": [
    # 1. the kit's mark beside Kit 1's
    ('PROCROOM = "S634"             # S634_PROCROOM_LIST: a Procedure room paper\'s lines -- product, quantity, brand, place; no rate (procroom.py)\n',
     'PROCROOM = "S634"             # S634_PROCROOM_LIST: a Procedure room paper\'s lines -- product, quantity, brand, place; no rate (procroom.py)\n'
     'PROCROOM_S635 = "S635"        # S635_PROCROOM_ORDERS: his order (counts nothing) and the slip joined to it, chosen in the same panel\n'),
    # 2. the Save hands the whole body to procroom, so its role and order are kept with its lines
    ('                return pr.save_lines(db, b, p.get("pr_lines") or [], _who(), _owner())\n',
     '                return pr.save_lines(db, b, p.get("pr_lines") or [], _who(), _owner(), p)       # S635: + pr_role, pr_order, pr_book\n'),
    # 3. the panel's state carries the paper's role, its order, the book page number
    ("saved:l.saved,orth:l.orth};})};}}",
     "saved:l.saved,orth:l.orth};}),role:j.pr.role||'slip',order:String(j.pr.order||''),book:j.pr.book||''};}}"),
    # 4. the role and the order, at the top of the panel (no rupee, no rate)
    ("var h='<b>Procedure room lines</b><span class=muted>Give each line its product, quantity and place. A line left without a product counts nothing. No rates here — Dr Manoj adds them.</span>';",
     "var h='<b>Procedure room lines</b><span class=muted>Give each line its product, quantity and place. A line left without a product counts nothing. No rates here — Dr Manoj adds them.</span>';"
     "\n var ro=S.pr.role=='order';h+='<div data-pr635=1 style=\"display:flex;flex-wrap:wrap;gap:12px;align-items:center\"><label style=\"margin:0;display:inline-flex;gap:5px;align-items:center;font-weight:normal\"><input type=radio name=prrole value=slip data-prr=1'+(ro?'':' checked')+' style=\"width:auto;margin:0\"> A slip or a bill (it counts)</label>'"
     "+'<label style=\"margin:0;display:inline-flex;gap:5px;align-items:center;font-weight:normal\"><input type=radio name=prrole value=order data-prr=1'+(ro?' checked':'')+' style=\"width:auto;margin:0\"> Dr Manoj’s order (it counts nothing)</label></div>';"
     "\n if(ro){h+='<div style=\"display:flex;flex-wrap:wrap;gap:6px;align-items:center\"><span>Book page no.</span><input data-prbk=1 value=\"'+esc(S.pr.book)+'\" placeholder=\"book page no.\" style=\"width:120px;font-size:13px;padding:4px\"><span class=muted>His signed order: its lines are kept and count nothing — the slip that comes against it counts.</span></div>';}"
     "\n else{var oo='<option value=\"\">— no order —</option>',ol=(j.pr.olines||{})[S.pr.order]||[];(j.pr.orders||[]).forEach(function(x){oo+='<option value=\"'+x.id+'\"'+(String(x.id)==S.pr.order?' selected':'')+'>'+esc(x.lab)+'</option>';});"
     "\n  h+='<div style=\"display:flex;flex-wrap:wrap;gap:6px;align-items:center\"><span>Against order</span><select data-pro=1 style=\"font-size:13px;padding:3px;max-width:340px\">'+oo+'</select>'+(ol.length?'<a href=\"#\" data-prfill=1 style=\"font-size:13px\">Fill the lines from this order</a>':'')+'</div>';}"),
    # 5. nothing read: say when the lines came from the order
    ("if(j.pr.noread){h+='<div class=muted>No items read — fill the line by hand.</div>';}",
     "if(j.pr.noread){h+='<div class=muted>'+(j.pr.filled?'No items read — filled from the order; correct anything that differs on the slip.':'No items read — fill the line by hand.')+'</div>';}"),
    # 6. the Save's body carries them
    ("brand:l.brand,place:l.place,item:l.item,sug:!!(l.sug&&!l.saved)};});}}",
     "brand:l.brand,place:l.place,item:l.item,sug:!!(l.sug&&!l.saved)};});b.pr_role=S.pr.role=='order'?'order':'slip';b.pr_order=S.pr.role=='order'?'':S.pr.order;b.pr_book=S.pr.role=='order'?S.pr.book:'';}}"),
    # 7. typing the book page number
    ("else if(t.hasAttribute('data-prb')){S.pr.lines[+t.getAttribute('data-prb')].brand=t.value;}});",
     "else if(t.hasAttribute('data-prb')){S.pr.lines[+t.getAttribute('data-prb')].brand=t.value;}else if(t.hasAttribute('data-prbk')){S.pr.book=t.value;}});"),
    # 8. choosing the role or the order repaints the panel
    ("else if(t.hasAttribute('data-prp')){var lp=S.pr.lines[+t.getAttribute('data-prp')];lp.place=t.value;lp.sug=false;s634flags();}});",
     "else if(t.hasAttribute('data-prp')){var lp=S.pr.lines[+t.getAttribute('data-prp')];lp.place=t.value;lp.sug=false;s634flags();}"
     "\n else if(t.hasAttribute('data-prr')||t.hasAttribute('data-pro')){if(t.hasAttribute('data-prr')){S.pr.role=t.value;}else{S.pr.order=t.value;}var bo=$('pr634');if(bo){bo.removeAttribute('data-for');}s634paint(S.cur);}});"),
    # 9. "Fill the lines from this order": the order's lines replace the panel's (suggestions; he corrects; nothing saved until Save)
    ("var bx=$('pr634');if(bx){bx.removeAttribute('data-for');}s634paint(S.cur);});\n// S571_BATTERIES",
     "var bx=$('pr634');if(bx){bx.removeAttribute('data-for');}s634paint(S.cur);});\n"
     "// S635_PROCROOM_ORDERS: the order's lines into the panel on one tap (product, quantity, brand, place -- no rate)\n"
     "document.addEventListener('click',function(e){var t=e.target.closest?e.target.closest('[data-prfill]'):null;if(!t||!S.pr||!S.cur||!S.cur.pr){return;}e.preventDefault();\n"
     " var ol=(S.cur.pr.olines||{})[S.pr.order]||[];if(!ol.length){return;}S.pr.lines=ol.map(function(x,k){return {no:k+1,name:x.name,qty:x.qty,unit:x.unit||'',brand:x.brand||'',place:x.place||'proc',item:String(x.item==null?'':x.item),hand:false,sug:true,saved:false,orth:x.place=='sanj'};});\n"
     " var bf=$('pr634');if(bf){bf.removeAttribute('data-for');}s634paint(S.cur);cue();});\n"
     "// S571_BATTERIES"),
]}


def md5b(b):
    return hashlib.md5(b).hexdigest()


def build(src, dst, out=print):
    os.makedirs(dst, exist_ok=True)
    total = 0
    for f, edits in EDITS.items():
        with open(os.path.join(src, f), "rb") as h:
            raw = h.read()
        if md5b(raw) != FROM_PIN[f]:
            out("%s: FROM is %s, not the pin %s -- STOP" % (f, md5b(raw)[:8], FROM_PIN[f][:8]))
            return 1
        t = raw.decode("utf-8")
        for i, (a, b) in enumerate(edits, 1):
            n = t.count(a)
            if n != 1:
                out("%s: edit %d anchor found %d times (must be 1) -- STOP" % (f, i, n))
                return 1
            t = t.replace(a, b)
        data = t.encode("utf-8")
        with open(os.path.join(dst, f), "wb") as h:
            h.write(data)
        total += len(edits)
        out("%s: %d counted edit(s), %s -> %s" % (f, len(edits), md5b(raw)[:8], md5b(data)))
    shutil.copyfile(os.path.join(HERE, "procroom.py"), os.path.join(dst, "procroom.py"))
    with open(os.path.join(dst, "procroom.py"), "rb") as h:
        out("procroom.py: the kit's whole file, %s" % md5b(h.read()))
    out("make_s635: %d counted edits in all, and procroom.py" % total)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(build(sys.argv[1], sys.argv[2]))
