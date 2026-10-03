#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s454p3b.py -- kit S454_BILL_REGISTER, folder P3B_FIRST_DAY (S454 section 18: what the first afternoon of use showed, 03-Oct). CLAUDE.md
rule 2: every live file built from its live bytes (every anchor exactly once, FROM -> TO pinned). No new file.

  porders_s454.py  18.1  one line on the staff's screens: "Ek scan mein ek hi bill." under "Naya bill scan karo" (the home) and under each
                         "Bill scan karo" on "Maal aaya?" (F-712; a second bill in one scan cannot be seen from what the asset app stores)
                   18.2  the arrival screen's button reads "Save kijiye" while any line is tapped "Kam aaya" or "Nahi mila"; "Maal aa gaya"
                         with every line "Aa gaya". What it writes does not change.
                   18.6  the owner's card "the system agreed on X of Y" says on what stock: "on Marg's stock" / "on the shelf figure"
  order_sheet.py   18.6  compare() keeps the basis it was taken on (order.stock_basis) beside the figure
  scan_register.py 18.3  a supplier's "P.L." is dropped like PVT and LTD (GUNINA PHARMACEUTICALS P.L. LTD. = GUNINA PHARMACEUTICALS)
  order_rules.py   18.4  an order that arrived by its bill's scan is on the way ONCE on marg too (in transit), as part 3 made it on count
  stock_watch.py   18.5  F-713: a credit note (bill CN...) is a return, not a sale, in the spine's sales reading (Spine.sales, the 90-day
                         pace, the roster's sales value) -- read apart, as shelf_figure does

    make_s454p3b.py --finance /root/finance --out DIR
"""
import argparse
import hashlib
import os

FROM = {"porders_s454.py": "eadbc8d3582991fa36ef3fde83253126", "order_sheet.py": "ebe1eb4b327c1a784e20174cda0abd4b",
        "scan_register.py": "8d100e60c467dab413830a251ef198fb", "order_rules.py": "1729e971982d0823f8d33b3976fa4d74",
        "stock_watch.py": "b429660ddc9a5291e261c5fa6fe652c0"}

# ============================================================================================================== porders_s454.py
PS = [('''    "back": ("← BACK", "← BACK"),
}''',
       '''    "back": ("← BACK", "← BACK"),
    "onebill": ("Ek scan mein ek hi bill.", "One bill per scan."), "save": ("Save kijiye", "Save"),     # S454 P3B (18.1, 18.2)
}'''),
      ('''         '<a class="big" id="scannew" href="%s">📷 %s</a>' % (esc(intake(back=P)), L(en, "scan_new"))]''',
       '''         '<a class="big" id="scannew" href="%s">📷 %s</a>' % (esc(intake(back=P)), L(en, "scan_new")),
         '<div class="mut onebill" style="text-align:center;margin-top:-4px">%s</div>' % L(en, "onebill")]      # S454 P3B (18.1, F-712)'''),
      ('''                 '<a class="big" style="min-height:52px;font-size:18px" href="%s">📷 %s</a>'
                 '<div class="lnk"><a href="%s/s454/maal/%d">%s</a></div></div>'
                 % (o["id"], esc(o["vendor"]), esc(L(en, "orderN", OS.ddmm(o["created_at"]), o["n"])),
                    esc(intake(o["vendor"], back=P + "/s454/maal")), L(en, "billscan"), P, o["id"], L(en, "nobill")))''',
       '''                 '<a class="big" style="min-height:52px;font-size:18px" href="%s">📷 %s</a>'
                 '<div class="mut onebill" style="text-align:center">%s</div>'                     # S454 P3B (18.1, F-712)
                 '<div class="lnk"><a href="%s/s454/maal/%d">%s</a></div></div>'
                 % (o["id"], esc(o["vendor"]), esc(L(en, "orderN", OS.ddmm(o["created_at"]), o["n"])),
                    esc(intake(o["vendor"], back=P + "/s454/maal")), L(en, "billscan"), L(en, "onebill"), P, o["id"], L(en, "nobill")))'''),
      ('''    h.append('<button class="big" id="maalok" onclick="arSave()">%s</button>' % L(en, "maal_ok"))''',
       '''    h.append('<button class="big" id="maalok" data-ok="%s" data-save="%s" onclick="arSave()">%s</button>'      # S454 P3B (18.2): "Save kijiye" while
             % (esc(L(en, "maal_ok")), esc(L(en, "save")), L(en, "maal_ok")))                         # a line is short or missing'''),
      ('''document.getElementById('ic'+id).textContent=(how==='ok'?'✓':'!');}''',
       '''document.getElementById('ic'+id).textContent=(how==='ok'?'✓':'!');arLabel();}
function arLabel(){var b=document.getElementById('maalok'),s=false;for(var k in HOW){if(HOW[k]==='short'||HOW[k]==='missing'){s=true;}}b.textContent=b.getAttribute(s?'data-save':'data-ok');}'''),
      ('''            h.append('<div %s id="s454cmp"><b>Orders of %s: the system agreed on %d of %d items with Darpan\\'s sheet</b>\'''',
       '''            h.append('<div %s id="s454cmp"><b>Orders of %s: the system agreed on %d of %d items with Darpan\\'s sheet</b> <span id="s454basis">%s</span>\''''),
      ('''                     % (st, esc(OS.dmy(ns["newest_date"])), c["x"], c["y"], rows,''',
       '''                     % (st, esc(OS.dmy(ns["newest_date"])), c["x"], c["y"], esc(_s454_basis_words(c)), rows,''')]
PS_APPEND = '''

# ==========================================================================================================================================
# S454_BILL_REGISTER P3B (03-Oct-2026, S454 18.6): the agreement card says on what stock the figure was taken. The figure is the record kept
# at the sheet's load and is not recomputed. A comparison stored before part 3 (placed 03-Oct 18:17:11 IST) was taken on Marg's stock;
# from P3B each one carries its own basis (order_sheet.compare).
# ==========================================================================================================================================
S454_P3_PLACED = "2026-10-03T18:17:11"


def _s454_basis_words(c):
    b = c.get("basis")
    if b not in ("count", "marg"):
        b = "count" if str(c.get("at") or "") >= S454_P3_PLACED else "marg"
    return "on the shelf figure" if b == "count" else "on Marg's stock"
# ---- S454 P3B end -------------------------------------------------------------------------------------------------------------------------
'''

# ============================================================================================================== order_sheet.py
OSE = [('''    out = dict(x=len(both), y=len(sheet), both=both, only_sheet=only_sheet, only_system=only_sys, as_on=p.get("as_on"), at=now_iso())''',
        '''    out = dict(x=len(both), y=len(sheet), both=both, only_sheet=only_sheet, only_system=only_sys, as_on=p.get("as_on"), at=now_iso(),
               basis=("marg" if setting(con, "order.stock_basis") == "marg" else "count"))   # S454 P3B (18.6): the stock the plan was taken on''')]

# ============================================================================================================== scan_register.py
SRE = [('''    t = re.sub(r"\\bM\\s*/\\s*S\\b\\.?", " ", t)
    t = t.replace("&", " AND ")''',
        '''    t = re.sub(r"\\bM\\s*/\\s*S\\b\\.?", " ", t)
    t = re.sub(r"(?<![A-Z0-9.])P\\s*\\.\\s*L\\b\\.?", " ", t)       # S454 P3B (18.3): a standalone "P.L." is dropped like PVT and LTD
    t = t.replace("&", " AND ")'''),
       ('''    """Upper case; punctuation and brackets dropped; '&' = AND; standalone PVT, LTD, P, CO, M/S dropped; a trailing BAREILLY dropped."""''',
        '''    """Upper case; punctuation and brackets dropped; '&' = AND; standalone PVT, LTD, P, CO, M/S and P.L. dropped; a trailing BAREILLY dropped."""''')]

# ============================================================================================================== order_rules.py
ORE = [('''    onord = _on_order_units(con, today)
    if basis == "count":''',
        '''    onord = _on_order_units(con, today, "count")             # S454 P3B (18.4): an order that arrived by its scan is on the way ONCE, on marg
    if basis == "count":                                       # too -- in transit (purchase_app._in_transit), never again as on order''')]

# ============================================================================================================== stock_watch.py
CN = "UPPER(COALESCE(bill,'')) LIKE 'CN%'"                       # a credit note's bill (the spine's SALE_RETURN, sp_move's ref)
CN2 = CN.replace("%", "%%")                                        # inside Spine.sales, whose string is %-formatted afterwards
SWE = [('''        r = self.q("SELECT COALESCE(SUM(units),0) AS u, COALESCE(SUM(CASE WHEN units<0 THEN -units ELSE 0 END),0) AS ret, "
                   "COALESCE(SUM(rate_p*units/NULLIF(CASE WHEN pack LIKE '1*%%' THEN CAST(substr(pack,3) AS REAL) ELSE 1 END,0)),0) AS v, COUNT(*) AS n, "
                   "COALESCE(SUM(CASE WHEN qty_raw LIKE '0:%%' THEN units ELSE 0 END),0) AS loose "''',
        '''        # S454 P3B (18.5, F-713): a credit note (bill CN...) carries positive units -- it is a RETURN: u = sales net of returns, ret = returns
        r = self.q("SELECT COALESCE(SUM(CASE WHEN {CN} THEN -units ELSE units END),0) AS u, "
                   "COALESCE(SUM(CASE WHEN {CN} THEN units WHEN units<0 THEN -units ELSE 0 END),0) AS ret, "
                   "COALESCE(SUM((CASE WHEN {CN} THEN -1 ELSE 1 END)*rate_p*units/NULLIF(CASE WHEN pack LIKE '1*%%' THEN CAST(substr(pack,3) AS REAL) ELSE 1 END,0)),0) AS v, "
                   "COALESCE(SUM(CASE WHEN {CN} THEN 0 ELSE 1 END),0) AS n, "
                   "COALESCE(SUM(CASE WHEN qty_raw LIKE '0:%%' AND NOT ({CN}) THEN units ELSE 0 END),0) AS loose "'''.replace("{CN}", CN2)),
       ('''    for r in sp.q("SELECT k20, COALESCE(SUM(units),0) AS u, COALESCE(SUM(CASE WHEN qty_raw LIKE '0:%' THEN units ELSE 0 END),0) AS loose, "
                  "COALESCE(SUM(rate_p*units/NULLIF(CASE WHEN pack LIKE '1*%' THEN CAST(substr(pack,3) AS REAL) ELSE 1 END,0)),0) AS v "''',
        '''    for r in sp.q("SELECT k20, COALESCE(SUM(CASE WHEN {CN} THEN -units ELSE units END),0) AS u, "     # S454 P3B (18.5): a credit note is a return
                  "COALESCE(SUM(CASE WHEN qty_raw LIKE '0:%' AND NOT ({CN}) THEN units ELSE 0 END),0) AS loose, "
                  "COALESCE(SUM((CASE WHEN {CN} THEN -1 ELSE 1 END)*rate_p*units/NULLIF(CASE WHEN pack LIKE '1*%' THEN CAST(substr(pack,3) AS REAL) ELSE 1 END,0)),0) AS v "'''
        .replace("{CN}", CN)),
       ('''    rows = sp.q("SELECT k20, COALESCE(SUM(rate_p*units/NULLIF(CASE WHEN pack LIKE '1*%' THEN CAST(substr(pack,3) AS REAL) ELSE 1 END,0)),0) AS v, COALESCE(SUM(units),0) AS u "''',
        '''    rows = sp.q("SELECT k20, COALESCE(SUM((CASE WHEN {CN} THEN -1 ELSE 1 END)*rate_p*units/NULLIF(CASE WHEN pack LIKE '1*%' THEN CAST(substr(pack,3) AS REAL) ELSE 1 END,0)),0) AS v, "
                "COALESCE(SUM(CASE WHEN {CN} THEN -units ELSE units END),0) AS u "              # S454 P3B (18.5): a credit note is a return'''
        .replace("{CN}", CN))]

EDITS = {"porders_s454.py": PS, "order_sheet.py": OSE, "scan_register.py": SRE, "order_rules.py": ORE, "stock_watch.py": SWE}
APPEND = {"porders_s454.py": PS_APPEND}
GUARD = "\nif __name__ == \"__main__\":"


def place_block(txt, block):
    """The block goes ABOVE the file's `if __name__ == "__main__":` guard when it has one (part 1D's lesson), else at the end."""
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


if __name__ == "__main__":
    main()
