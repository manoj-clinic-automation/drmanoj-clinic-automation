"""
t_sizeprior.py -- S219: the scanner is TOLD the page size.

The owner measured that >95% of pharmacy purchase bills are HALF A4 (A5,
148x210mm, aspect 0.705).  With that declared, a candidate box that is not that
shape is refused -- and the text block inside a bill never is, because margins
make it wider and shorter than the page.

Same sweep as t_fillframe.py, run twice: without the prior (today's behaviour,
which must be untouched) and with it.  What must be true WITH the prior:

  * in the good band the page is still found, as accurately as before
  * where it used to return a confident, plausible box around the PRINTING it
    now refuses -- and refusing hands the user the guide rectangle, which is the
    right shape in roughly the right place

USAGE: python3 -B t_sizeprior.py
"""
from playwright.sync_api import sync_playwright
import math, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
A5 = 148.0 / 210.0          # 0.7048

MAKE = r"""
(spec) => {
  // S219: seeded PRNG. The original harness used rnd() for the printed
  // lines and the desk noise, so two runs of the same case drew different
  // images and results wandered between runs. A test pinned to a moving number
  // teaches people to ignore it; this one is now reproducible.
  let _s = 12345;
  const rnd = () => { _s = (_s * 1103515245 + 12345) & 0x7fffffff; return _s / 0x7fffffff; };
  const c = document.createElement('canvas');
  c.width = spec.W; c.height = spec.H;
  const g = c.getContext('2d');
  g.fillStyle = spec.bg; g.fillRect(0,0,spec.W,spec.H);
  if (spec.noise) {
    for (let i=0;i<spec.noise;i++){
      g.fillStyle = 'rgba(0,0,0,'+(0.03+rnd()*0.05)+')';
      g.fillRect(rnd()*spec.W, rnd()*spec.H, 6, 6);
    }
  }
  const [x,y,w,h] = spec.rect;
  g.fillStyle = spec.card; g.fillRect(x,y,w,h);
  // printing inside the card -- the thing that must NOT move the outline
  g.fillStyle = '#222';
  for (let i=0;i<spec.lines;i++){
    const ly = y + h*0.15 + i*(h*0.66/Math.max(1,spec.lines));
    g.fillRect(x + w*0.08, ly, w*(0.35+rnd()*0.5), Math.max(2, h*0.045));
  }
  if (spec.photo) { g.fillStyle='#557'; g.fillRect(x+w*0.70, y+h*0.15, w*0.22, h*0.45); }
  return window.__scannerAutoDetect(c);
}
"""

# S219 probe: a HALF-A4 PHARMACY BILL swept across how much of the frame it
# fills, on a white surface and a dark one -- the owner reported autocrop not
# firing on exactly this, on BOTH backgrounds.
import math as _m

HOST = """<!doctype html><html><head><meta charset=utf-8></head><body>
<div id=scanroot></div>
<script>window.jspdf={jsPDF:function(){return{addImage:function(){},addPage:function(){},
save:function(){},output:function(){return new Blob(["p"],{type:"application/pdf"});},
internal:{pageSize:{getWidth:function(){return 210;},getHeight:function(){return 297;}}}};}};</script>
<script>window.SCANNER_CONFIG = __CFG__;</script>
<script src="scanner_widget.js"></script></body></html>"""

CASES = []
for _fill, _tag in ((0.45,"45%"),(0.60,"60%"),(0.70,"70%"),(0.80,"80%"),
                    (0.88,"88%"),(0.93,"93%"),(0.96,"96%"),(0.99,"99%")):
    _W,_H = 900,1200
    _h = int(math.sqrt(_fill*_W*_H/A5)); _w = int(_h*A5)
    _w,_h = min(_w,_W), min(_h,_H)
    _x,_y = (_W-_w)//2, (_H-_h)//2
    for _bg,_bt in (("#f2f2f0","LIGHT"),("#20242a","DARK ")):
        CASES.append(("bill %-5s %s" % (_tag,_bt), _W,_H,(_x,_y,_w,_h), _bg, "#ffffff", 14, False, 0))

def run(cfg, label):
    out = {}
    page_html = HOST.replace("__CFG__", cfg)
    f = HERE / "_sp.html"; f.write_text(page_html, encoding="utf-8")
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(viewport={"width":390,"height":780})
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(f.as_uri()); pg.wait_for_timeout(300)
        if errs: print("  !! page errors:", errs[:2])
        for name,W,H,rect,bg,card,lines,photo,noise in CASES:
            got = pg.evaluate(MAKE, {"W":W,"H":H,"rect":list(rect),"bg":bg,"card":card,
                                     "lines":lines,"photo":photo,"noise":noise})
            if not got:
                out[name] = None; continue
            x,y,w,h = rect
            fx,fy = got[0]; gx,gy = got[2]
            fw,fh = gx-fx, gy-fy
            out[name] = max(abs(fx-x),abs(fy-y),abs(fw-w),abs(fh-h))/max(w,h)
        b.close()
    f.unlink()
    return out

NOPRIOR = run('{title:"t",uploadUrl:"/u",fileField:"f",nameBase:"n",backUrl:"/"}', "no prior")
PRIOR   = run('{title:"t",uploadUrl:"/u",fileField:"f",nameBase:"n",backUrl:"/",'
              'expectAspect:0.7048,expectLabel:"half-A4 bill"}', "with prior")

print("%-16s %-22s %s" % ("case", "no prior (today)", "WITH the half-A4 prior"))
bad = []
for name,_W,_H,_r,_bg,_c,_l,_p,_n in CASES:
    a, bb = NOPRIOR[name], PRIOR[name]
    fa = "refused" if a is None else "%5.1f%%" % (a*100)
    fb = "refused -> guide" if bb is None else "%5.1f%%" % (bb*100)
    flag = ""
    if a is not None and a <= 0.06 and (bb is None or bb > 0.06):
        flag = "  <-- REGRESSION"; bad.append(name)
    if a is not None and a > 0.06 and bb is None:
        flag = "  <-- confident-wrong box now refused"
    print("%-16s %-22s %s%s" % (name, fa, fb, flag))

good_kept = sum(1 for n in PRIOR if NOPRIOR[n] is not None and NOPRIOR[n] <= 0.06
                and PRIOR[n] is not None and PRIOR[n] <= 0.06)
good_total = sum(1 for n in NOPRIOR if NOPRIOR[n] is not None and NOPRIOR[n] <= 0.06)
wrong_before = sum(1 for n in NOPRIOR if NOPRIOR[n] is not None and NOPRIOR[n] > 0.06)
wrong_after = sum(1 for n in PRIOR if PRIOR[n] is not None and PRIOR[n] > 0.06)
print()
print("  accurate detections kept : %d of %d" % (good_kept, good_total))
print("  confident-WRONG boxes    : %d  ->  %d" % (wrong_before, wrong_after))
print()
if bad:
    print("SIZE PRIOR RED -- it cost a good detection: %s" % ", ".join(bad)); sys.exit(1)
if wrong_after >= wrong_before:
    print("SIZE PRIOR RED -- it did not remove the wrong boxes"); sys.exit(1)
print("SIZE PRIOR GREEN -- every good detection kept, %d wrong box(es) removed"
      % (wrong_before - wrong_after))
