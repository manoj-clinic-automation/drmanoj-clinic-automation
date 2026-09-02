"""Is the button you must press next actually on the screen?"""
from playwright.sync_api import sync_playwright
import pathlib as _pl
_HOST = (_pl.Path(__file__).resolve().parent / "host.html").as_uri()

FAKE_CAM = r"""
(() => {
  // a fake camera that returns a PORTRAIT stream -- the case that broke it
  const c = document.createElement('canvas'); c.width = 1080; c.height = 1440;
  const g = c.getContext('2d');
  (function draw(){ g.fillStyle='#345'; g.fillRect(0,0,c.width,c.height);
    g.fillStyle='#fff'; g.fillRect(240,420,600,380);
    requestAnimationFrame(draw); })();
  const stream = c.captureStream(12);
  // file:// is not a secure origin, so navigator.mediaDevices does not exist --
  // define it, or the widget correctly hides the camera button and the test
  // clicks something invisible and proves nothing.
  if (!navigator.mediaDevices) {
    Object.defineProperty(navigator, 'mediaDevices', {value:{}, configurable:true});
  }
  // A plain assignment did not take -- the real getUserMedia kept being called
  // and answered NotFoundError, so the test was proving nothing. Override on
  // the PROTOTYPE, which is where the method actually lives.
  const proto = Object.getPrototypeOf(navigator.mediaDevices) || navigator.mediaDevices;
  Object.defineProperty(proto, 'getUserMedia',
    {value: () => Promise.resolve(stream), configurable: true, writable: true});
  Object.defineProperty(proto, 'enumerateDevices',
    {value: () => Promise.resolve([]), configurable: true, writable: true});
})();
"""

PHONES = [("small phone", 360, 640), ("common phone", 390, 780), ("large phone", 430, 900)]

def vis(pg, sel):
    return pg.evaluate("""(s)=>{const e=document.querySelector(s); if(!e) return null;
      const r=e.getBoundingClientRect();
      return {top:Math.round(r.top),bottom:Math.round(r.bottom),h:Math.round(r.height),
              w:Math.round(r.width),inView:(r.top < innerHeight && r.bottom > 0)};}""", sel)

with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--use-fake-ui-for-media-stream"])
    for name, W, H in PHONES:
        pg = b.new_page(viewport={"width": W, "height": H})
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.add_init_script(FAKE_CAM)
        pg.goto(_HOST); pg.wait_for_timeout(250)
        print("\n=== %s  %dx%d ===" % (name, W, H))
        if errs: print("  PAGE ERRORS:", errs)
        pg.click("#opencam"); pg.wait_for_timeout(900)
        v = vis(pg, "#vid"); cap = vis(pg, "#shootbtn")
        print("  video      %4d px tall  (viewport %d)" % (v["h"], H))
        print("  Capture    top=%4d  %s" % (cap["top"],
              "ON SCREEN without scrolling" if cap["bottom"] <= H and cap["top"] >= 0
              else "OFF SCREEN -- would need scrolling"))
        # capture a frame, then check the stage and Save
        pg.click("#shootbtn"); pg.wait_for_timeout(700)
        add = vis(pg, "#addpage")
        print("  Add page   %d px tall, width %d" % (add["h"], add["w"]))
        pg.click("#addpage"); pg.wait_for_timeout(500)
        sv = vis(pg, "#savebtn")
        print("  Save       top=%4d h=%d  %s" % (sv["top"], sv["h"],
              "ON SCREEN (sticky)" if sv["bottom"] <= H + 1 and sv["top"] >= 0 else "off screen"))
        small = pg.evaluate("""()=>{const out=[];
          document.querySelectorAll('#scanroot button,#scanroot .btn,#scanroot input[type=text]')
            .forEach(e=>{const r=e.getBoundingClientRect();
              if(r.height>0 && r.height<44) out.push((e.id||e.className)+' '+Math.round(r.height)+'px');});
          return out;}""")
        print("  tap targets under 44px: %s" % (", ".join(small) if small else "none"))
        pg.close()
    b.close()
