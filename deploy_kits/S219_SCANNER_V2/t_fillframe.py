"""
t_fillframe.py -- S219: how much of the frame may the document fill?

THE OWNER'S REPORT, 02-Sep-2026, scanning a real half-A4 pharmacy bill:
autocrop did not fire -- "even on the white background and on a dark background
with nothing around it."

This reproduces it.  A half-A4 (A5, 148x210mm) bill is swept across the share of
the frame it occupies, on a light surface and a dark one.  The result is not
about the background at all -- it is about SIZE IN FRAME:

    up to 80% of the frame   detected to 0.1-0.3%   -- excellent
    88% and beyond, DARK     REFUSED -> the 8% inset, i.e. no autocrop
    88% and beyond, LIGHT    the box lands on the TEXT BLOCK, ~34% too small,
                             and looks entirely plausible

The second is the dangerous one, and v2's own comment names the mechanism: when
the document fills the frame the ring samples the DOCUMENT, the paper becomes
the fitted "surface", and the only thing left standing out is the printing.  The
edge-step guard written to catch exactly this is fooled by the outermost line of
text, which does present a step.

Any fix must keep every row of this file green.
"""
from playwright.sync_api import sync_playwright
import pathlib as _pl
_HOST = (_pl.Path(__file__).resolve().parent / "host.html").as_uri()
import json

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
CASES = []
for _fill, _tag in ((0.45,"45%"),(0.60,"60%"),(0.70,"70%"),(0.80,"80%"),
                    (0.88,"88%"),(0.93,"93%"),(0.96,"96%"),(0.99,"99%")):
    _W,_H = 900,1200
    _h = int(_m.sqrt(_fill*_W*_H/0.705)); _w = int(_h*0.705)
    _w,_h = min(_w,_W), min(_h,_H)
    _x,_y = (_W-_w)//2, (_H-_h)//2
    for _bg,_bt in (("#f2f2f0","WHITE surface"),("#20242a","DARK surface")):
        CASES.append(("bill %-6s of frame, %s" % (_tag,_bt), _W,_H,(_x,_y,_w,_h),
                      _bg, "#ffffff", 14, False, 0))
REFUSE = []

with sync_playwright() as pw:
    b = pw.chromium.launch(); pg = b.new_page(viewport={"width":390,"height":780})
    errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(_HOST); pg.wait_for_timeout(300)
    print("page errors on load:", errs if errs else "none")
    print()
    print("%-30s %-22s %-22s %s" % ("case","truth (x,y,w,h)","found","worst edge error"))
    ok=0; total=0
    for name,W,H,rect,bg,card,lines,photo,noise in CASES:
        total+=1
        got = pg.evaluate(MAKE, {"W":W,"H":H,"rect":list(rect),"bg":bg,"card":card,
                                 "lines":lines,"photo":photo,"noise":noise})
        if not got:
            print("%-30s %-22s %-22s REFUSED" % (name, rect, "-")); continue
        x,y,w,h = rect
        fx,fy = got[0]; gx,gy = got[2]
        fw,fh = gx-fx, gy-fy
        # error as a fraction of the card's own size
        e = max(abs(fx-x), abs(fy-y), abs(fw-w), abs(fh-h)) / max(w,h)
        good = e <= 0.06
        ok += 1 if good else 0
        print("%-30s %-22s %-22s %5.1f%%  %s" % (name, "%d,%d,%d,%d"%rect,
              "%d,%d,%d,%d"%(round(fx),round(fy),round(fw),round(fh)), e*100,
              "ok" if good else "OFF"))
    print()
    for name,W,H,rect,bg,card,lines,photo,noise in REFUSE:
        got = pg.evaluate(MAKE, {"W":W,"H":H,"rect":list(rect),"bg":bg,"card":card,
                                 "lines":lines,"photo":photo,"noise":noise})
        print("%-30s -> %s" % (name, "REFUSED (falls back to the 8%% inset)" if not got else "DETECTED %s -- WRONG" % got))
    print("\n%d/%d within 6%% of the true edges" % (ok, total))
    b.close()
