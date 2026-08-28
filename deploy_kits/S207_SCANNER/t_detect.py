"""Autodetect accuracy against synthetic documents with known ground truth."""
from playwright.sync_api import sync_playwright
import json

MAKE = r"""
(spec) => {
  const c = document.createElement('canvas');
  c.width = spec.W; c.height = spec.H;
  const g = c.getContext('2d');
  g.fillStyle = spec.bg; g.fillRect(0,0,spec.W,spec.H);
  if (spec.noise) {
    for (let i=0;i<spec.noise;i++){
      g.fillStyle = 'rgba(0,0,0,'+(0.03+Math.random()*0.05)+')';
      g.fillRect(Math.random()*spec.W, Math.random()*spec.H, 6, 6);
    }
  }
  const [x,y,w,h] = spec.rect;
  g.fillStyle = spec.card; g.fillRect(x,y,w,h);
  // printing inside the card -- the thing that must NOT move the outline
  g.fillStyle = '#222';
  for (let i=0;i<spec.lines;i++){
    const ly = y + h*0.15 + i*(h*0.66/Math.max(1,spec.lines));
    g.fillRect(x + w*0.08, ly, w*(0.35+Math.random()*0.5), Math.max(2, h*0.045));
  }
  if (spec.photo) { g.fillStyle='#557'; g.fillRect(x+w*0.70, y+h*0.15, w*0.22, h*0.45); }
  return window.__scannerAutoDetect(c);
}
"""

CASES = [
  # name,                       W,   H,   rect(x,y,w,h),        bg,        card,    lines, photo, noise
  ("licence, centred",          1200, 900, (300,240,600,380),  "#c9cdd4", "#ffffff", 5, True, 0),
  ("licence, small in frame",   1200, 900, (430,330,340,215),  "#b8bcc4", "#ffffff", 4, True, 0),
  ("licence, off to one side",  1200, 900, (120,150,520,330),  "#c9cdd4", "#fdfdfd", 5, True, 0),
  ("A4 page, fills most",       1000,1400, ( 90,120,820,1160), "#9aa0aa", "#ffffff", 12, False, 0),
  ("card on a busy desk",       1200, 900, (330,260,560,350),  "#c0c4cc", "#ffffff", 5, True, 260),
  ("low contrast, grey on grey",1200, 900, (300,240,600,380),  "#b0b4bb", "#d8dbe0", 5, True, 0),
  ("portrait phone shot",        900,1200, (150,300,600,380),  "#c9cdd4", "#ffffff", 5, True, 0),
]
REFUSE = [
  ("blank frame, nothing there", 1200, 900, (0,0,0,0), "#c9cdd4", "#c9cdd4", 0, False, 0),
]

with sync_playwright() as pw:
    b = pw.chromium.launch(); pg = b.new_page(viewport={"width":390,"height":780})
    errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto("file:///home/claude/scan/host.html"); pg.wait_for_timeout(300)
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
