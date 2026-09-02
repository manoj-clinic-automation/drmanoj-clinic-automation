"""Adversarial cases: what a phone in a pharmacy actually produces."""
from playwright.sync_api import sync_playwright
import pathlib as _pl
_HOST = (_pl.Path(__file__).resolve().parent / "host.html").as_uri()

MAKE = r"""
(s) => {
  const c=document.createElement('canvas'); c.width=s.W; c.height=s.H;
  const g=c.getContext('2d');
  g.fillStyle=s.bg; g.fillRect(0,0,s.W,s.H);
  if (s.shadow){                                   // uneven light across the desk
    const lg=g.createLinearGradient(0,0,s.W,s.H);
    lg.addColorStop(0,'rgba(0,0,0,0)'); lg.addColorStop(1,'rgba(0,0,0,'+s.shadow+')');
    g.fillStyle=lg; g.fillRect(0,0,s.W,s.H);
  }
  if (s.vignette){
    const rg=g.createRadialGradient(s.W/2,s.H/2,Math.min(s.W,s.H)*0.2,s.W/2,s.H/2,Math.max(s.W,s.H)*0.7);
    rg.addColorStop(0,'rgba(0,0,0,0)'); rg.addColorStop(1,'rgba(0,0,0,'+s.vignette+')');
    g.fillStyle=rg; g.fillRect(0,0,s.W,s.H);
  }
  if (s.finger){ g.fillStyle='#b08868'; g.fillRect(0, s.H*0.55, s.W*0.10, s.H*0.30); }
  const [x,y,w,h]=s.rect;
  g.save();
  if (s.tilt){ g.translate(x+w/2,y+h/2); g.rotate(s.tilt*Math.PI/180); g.translate(-(x+w/2),-(y+h/2)); }
  g.fillStyle=s.card; g.fillRect(x,y,w,h);
  g.fillStyle='#222';
  for(let i=0;i<s.lines;i++){
    const ly=y+h*0.15+i*(h*0.66/Math.max(1,s.lines));
    g.fillRect(x+w*0.08, ly, w*(0.35+((i*37)%50)/100), Math.max(2,h*0.045));
  }
  g.restore();
  const r = window.__scannerAutoDetect(c);
  return {r:r, W:s.W, H:s.H};
}
"""
CASES=[
 dict(n="tilted 8 degrees",      W=1200,H=900, rect=(300,240,600,380), bg="#c9cdd4", card="#ffffff", lines=5, tilt=8),
 dict(n="tilted 20 degrees",     W=1200,H=900, rect=(300,240,600,380), bg="#c9cdd4", card="#ffffff", lines=5, tilt=20),
 dict(n="strong shadow gradient",W=1200,H=900, rect=(300,240,600,380), bg="#c9cdd4", card="#ffffff", lines=5, shadow=0.45),
 dict(n="vignette (phone flash)",W=1200,H=900, rect=(300,240,600,380), bg="#c9cdd4", card="#ffffff", lines=5, vignette=0.5),
 dict(n="dark desk, white card", W=1200,H=900, rect=(300,240,600,380), bg="#2c2f36", card="#fdfdfd", lines=5),
 dict(n="white desk, white card",W=1200,H=900, rect=(300,240,600,380), bg="#fbfbfb", card="#ffffff", lines=5),
 dict(n="finger at the edge",    W=1200,H=900, rect=(330,240,560,380), bg="#c9cdd4", card="#ffffff", lines=5, finger=1),
 dict(n="card touching the edge",W=1200,H=900, rect=(0,200,700,420),   bg="#c9cdd4", card="#ffffff", lines=5),
 dict(n="card fills the frame",  W=1200,H=900, rect=(0,0,1200,900),    bg="#c9cdd4", card="#ffffff", lines=8),
]
with sync_playwright() as pw:
    b=pw.chromium.launch(); pg=b.new_page(viewport={"width":390,"height":780})
    pg.goto(_HOST); pg.wait_for_timeout(250)
    print("%-26s %-22s %-22s %s" % ("case","truth","found","verdict"))
    for cse in CASES:
        s=dict(W=cse["W"],H=cse["H"],rect=list(cse["rect"]),bg=cse["bg"],card=cse["card"],
               lines=cse["lines"],tilt=cse.get("tilt",0),shadow=cse.get("shadow",0),
               vignette=cse.get("vignette",0),finger=cse.get("finger",0))
        out=pg.evaluate(MAKE,s); r=out["r"]; x,y,w,h=cse["rect"]
        if not r:
            print("%-26s %-22s %-22s refused -> manual corners" % (cse["n"],"%d,%d,%d,%d"%(x,y,w,h),"-")); continue
        fx,fy=r[0]; gx,gy=r[2]; fw,fh=gx-fx,gy-fy
        # for a tilted card the true bounding box grows; compare to that
        e=max(abs(fx-x),abs(fy-y),abs(fw-w),abs(fh-h))/max(w,h)
        tag = "ok" if e<=0.06 else ("loose (%.0f%%) - drag to fix" % (e*100) if e<=0.25 else "OFF %.0f%%"%(e*100))
        print("%-26s %-22s %-22s %s" % (cse["n"],"%d,%d,%d,%d"%(x,y,w,h),
              "%d,%d,%d,%d"%(round(fx),round(fy),round(fw),round(fh)), tag))
    b.close()
