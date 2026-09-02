"""
t_presets.py -- S219: does "Medical bill (A5)" put the outline ON the bill?

The owner's report after the size prior went live: scanning in the asset app,
"vertically its very much extra area captured".  That was the FALLBACK guide --
a fixed 80% of the frame -- not the detector.  A guide sized by guesswork
overshoots whenever the bill sits smaller than the guess.

So the preset does not use a fixed fraction.  It finds the bright region (the
paper), then places a rectangle of the chosen aspect over it.  This asserts
that placement against bills drawn at known positions and sizes.

USAGE: python3 -B t_presets.py
"""
from playwright.sync_api import sync_playwright
import json, math, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
A5 = 148.0 / 210.0

DRAW = r"""
(spec) => {
  // the widget keeps two stacked canvases: cv holds the photo, ov the outline.
  // BOTH must be sized, or the fit runs against an overlay of the wrong size --
  // which is exactly what this harness got wrong first time round.
  const cv = document.getElementById('cv');
  const ov = document.getElementById('ov');
  cv.width = spec.W; cv.height = spec.H;
  ov.width = spec.W; ov.height = spec.H;
  const g = cv.getContext('2d');
  g.fillStyle = spec.bg; g.fillRect(0,0,spec.W,spec.H);
  const [x,y,w,h] = spec.rect;
  g.fillStyle = '#ffffff'; g.fillRect(x,y,w,h);
  g.fillStyle = '#222';
  for (let i=0;i<12;i++) g.fillRect(x+w*0.08, y+h*0.12+i*(h*0.06), w*0.6, Math.max(2,h*0.02));
  return window.__scannerFit(spec.ar);
}
"""

HOST = """<!doctype html><html><head><meta charset=utf-8></head><body>
<div id=scanroot></div>
<script>window.jspdf={jsPDF:function(){return{addImage:function(){},addPage:function(){},
save:function(){},output:function(){return new Blob(["p"],{type:"application/pdf"});},
internal:{pageSize:{getWidth:function(){return 210;},getHeight:function(){return 297;}}}};}};</script>
<script>window.SCANNER_CONFIG={title:"t",uploadUrl:"/u",fileField:"f",nameBase:"n",backUrl:"/"};</script>
<script src="scanner_widget.js"></script></body></html>"""

CHECKS = []
def ck(n, c): CHECKS.append((n, bool(c)))

# a bill placed at known spots, at sizes a person actually shoots
CASES = [
    ("bill half the frame, centred",      900,1200, (225,300,450,638)),
    ("bill small, high in the frame",     900,1200, (280,120,340,482)),
    ("bill three-quarters",               900,1200, (135,180,630,893)),
    ("bill off to the left",              900,1200, ( 60,300,420,596)),
]

f = HERE / "_pre.html"; f.write_text(HOST, encoding="utf-8")
with sync_playwright() as pw:
    b = pw.chromium.launch(); pg = b.new_page(viewport={"width":390,"height":780})
    errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(f.as_uri()); pg.wait_for_timeout(300)
    ck("widget loaded with no error", not errs)
    print("%-34s %-22s %-22s %s" % ("case","bill (x,y,w,h)","outline placed","verdict"))
    for name,W,H,rect in CASES:
        got = pg.evaluate(DRAW, {"W":W,"H":H,"rect":list(rect),"bg":"#c9cdd4","ar":A5})
        x,y,w,h = rect
        L,T = got[0]; R,B = got[2]
        ow, oh = R-L, B-T
        ar = ow/oh if oh else 0
        # it must COVER the bill and not wander far beyond it
        covers = L <= x+2 and T <= y+2 and R >= x+w-2 and B >= y+h-2
        area_ratio = (ow*oh) / float(w*h)
        shape_ok = abs(ar - A5)/A5 < 0.02
        good = covers and shape_ok and area_ratio < 1.6
        ck("%s - covers the bill" % name, covers)
        ck("%s - correct A5 shape" % name, shape_ok)
        ck("%s - no gross overshoot (<1.6x area)" % name, area_ratio < 1.6)
        print("%-34s %-22s %-22s %s (%.2fx area)" % (
            name, "%d,%d,%d,%d"%rect, "%d,%d,%d,%d"%(round(L),round(T),round(ow),round(oh)),
            "ok" if good else "OFF", area_ratio))
    # Free must leave the outline alone
    before = pg.evaluate("window.__scannerCorners()")
    pg.evaluate("window.__scannerFit(0)")
    ck("'Free' changes nothing", pg.evaluate("window.__scannerCorners()") == before)
    # and the choice is remembered for the next bill in the pile
    pg.evaluate("window.__scannerFit(%f)" % A5)
    ck("the chosen size is remembered", pg.evaluate("localStorage.getItem('scanPresetAR')") is not None)
    b.close()
f.unlink()

bad = [n for n,ok in CHECKS if not ok]
print()
for n,ok in CHECKS:
    if not ok: print("  FAIL  %s" % n)
print("%d/%d checks passed" % (len(CHECKS)-len(bad), len(CHECKS)))
print("PRESETS " + ("GREEN" if not bad else "RED"))
sys.exit(1 if bad else 0)
