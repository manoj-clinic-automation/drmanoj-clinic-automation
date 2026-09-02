"""Everything v1 did must still do it. v2 changed layout and corner placement only."""
from playwright.sync_api import sync_playwright
import pathlib as _pl
_HOST = (_pl.Path(__file__).resolve().parent / "host.html").as_uri()

FAKE = r"""
(() => {
  const c=document.createElement('canvas'); c.width=1080; c.height=1440;
  const g=c.getContext('2d');
  (function d(){ g.fillStyle='#c9cdd4'; g.fillRect(0,0,1080,1440);
    g.fillStyle='#fff'; g.fillRect(240,420,600,380);
    g.fillStyle='#222'; for(let i=0;i<5;i++) g.fillRect(280,470+i*60,420,14);
    requestAnimationFrame(d); })();
  const stream=c.captureStream(12);
  if(!navigator.mediaDevices) Object.defineProperty(navigator,'mediaDevices',{value:{},configurable:true});
  const proto=Object.getPrototypeOf(navigator.mediaDevices)||navigator.mediaDevices;
  Object.defineProperty(proto,'getUserMedia',{value:()=>Promise.resolve(stream),configurable:true,writable:true});
  Object.defineProperty(proto,'enumerateDevices',{value:()=>Promise.resolve([]),configurable:true,writable:true});
})();
"""
fails=[]; passes=[0]
def ck(label, cond, detail=""):
    if cond: passes[0]+=1; print("  ok   %s"%label)
    else: fails.append(label); print("  FAIL %s  %s"%(label,detail))

with sync_playwright() as pw:
    b=pw.chromium.launch(); pg=b.new_page(viewport={"width":390,"height":780})
    errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
    uploads=[]
    def handle(route):
        uploads.append(route.request.url)
        route.fulfill(status=200, content_type="application/json", body='{"ok":true}')
    pg.route("**/files/upload", handle)
    pg.add_init_script(FAKE)
    pg.goto(_HOST); pg.wait_for_timeout(300)

    print("[1] the page still builds")
    ck("no errors on load", not errs, errs)
    for i in ["opencam","cam","shootbtn","addpage","addwhole","resetcorners","retake",
              "savebtn","fname","pages","modebar","hint","cambar","savebar","vid","cv","ov"]:
        ck("#%s exists"%i, pg.query_selector("#"+i) is not None)

    print("\n[2] every listener has something to bind to")
    missing = pg.evaluate("""()=>{const ids=['opencam','cam','shootbtn','cancelcam','addpage',
      'addwhole','resetcorners','retake','savebtn','fname','bw'];
      return ids.filter(i=>!document.getElementById(i));}""")
    ck("no listener binds to a missing element", missing==[], missing)

    print("\n[3] capture, auto-outline, add page, save")
    pg.click("#opencam"); pg.wait_for_timeout(900)
    pg.click("#shootbtn"); pg.wait_for_timeout(800)
    ck("the stage opened", pg.evaluate("()=>document.getElementById('stage').style.display")=="block")
    msg = pg.evaluate("()=>document.getElementById('msg').textContent")
    ck("it says what it did with the outline", "utline" in msg or "edges" in msg, msg)
    corners = pg.evaluate("""()=>{const ov=document.getElementById('ov');
      return {w:ov.width,h:ov.height};}""")
    ck("the overlay canvas is sized", corners["w"]>0 and corners["h"]>0, corners)

    # END TO END: the fake camera draws a white card at 240,420 600x380 inside a
    # 1080x1440 frame. loadImage scales the long side to 1400, so the card should
    # land near 233,408 583x369 on the working canvas. This is the assertion that
    # actually matters -- it proves the outline reaches the card through the real
    # capture path, not just that a function returns numbers.
    box = pg.evaluate("""()=>{const c=window.__scannerDebug; return null;}""")
    got = pg.evaluate("""()=>{
      const cv=document.getElementById('cv');
      const r=window.__scannerAutoDetect(cv);
      return r ? {x:r[0][0], y:r[0][1], w:r[2][0]-r[0][0], h:r[2][1]-r[0][1],
                  cw:cv.width, ch:cv.height} : null;}""")
    if got:
        sc = got["cw"]/1080.0
        ex = [240*sc, 420*sc, 600*sc, 380*sc]
        err = max(abs(got["x"]-ex[0]), abs(got["y"]-ex[1]),
                  abs(got["w"]-ex[2]), abs(got["h"]-ex[3]))/max(ex[2],ex[3])
        ck("the outline lands ON THE CARD through the real capture path (%.1f%% out)"%(err*100),
           err<=0.06, "got %s expected %s"%([round(v) for v in [got["x"],got["y"],got["w"],got["h"]]],
                                            [round(v) for v in ex]))
    else:
        ck("the outline lands on the card through the real capture path", False, "refused")
    pg.click("#addpage"); pg.wait_for_timeout(500)
    ck("a page was added", pg.evaluate("()=>document.querySelectorAll('#pages img').length")>=1)
    ck("the save bar appeared",
       pg.evaluate("()=>document.getElementById('savebar').style.display")=="block")
    ck("the filename is pre-filled",
       len(pg.evaluate("()=>document.getElementById('fname').value"))>0)
    ck("Save is enabled once there is a page",
       pg.evaluate("()=>!document.getElementById('savebtn').disabled"))

    print("\n[4] the other stage buttons still work")
    pg.click("#opencam"); pg.wait_for_timeout(700); pg.click("#shootbtn"); pg.wait_for_timeout(700)
    before = pg.evaluate("()=>document.getElementById('msg').textContent")
    pg.click("#resetcorners"); pg.wait_for_timeout(200)
    ck("reset outline does not throw", not [e for e in errs if "reset" in e.lower()])
    pg.click("#addwhole"); pg.wait_for_timeout(500)
    ck("whole image adds a second page",
       pg.evaluate("()=>document.querySelectorAll('#pages img').length")>=2)
    pg.click("#opencam"); pg.wait_for_timeout(700); pg.click("#shootbtn"); pg.wait_for_timeout(700)
    pg.click("#retake"); pg.wait_for_timeout(300)
    ck("retake closes the stage",
       pg.evaluate("()=>document.getElementById('stage').style.display")=="none")

    print("\n[5] the three modes still switch")
    for m in ["idcard","batch","doc"]:
        pg.evaluate("(m)=>{const r=[...document.getElementsByName('scanmode')].find(x=>x.value===m);"
                    "r.checked=true; r.dispatchEvent(new Event('change',{bubbles:true}));}", m)
        pg.wait_for_timeout(200)
        h = pg.evaluate("()=>document.getElementById('hint').textContent")
        ck("mode %s sets its own hint"%m, len(h)>10, h)

    print("\n[6] the camera tidies up after itself")
    pg.click("#opencam"); pg.wait_for_timeout(700)
    ck("chrome is hidden while aiming",
       pg.evaluate("()=>document.getElementById('modebar').style.display")=="none")
    pg.click("#cancelcam"); pg.wait_for_timeout(300)
    ck("and comes back on cancel",
       pg.evaluate("()=>document.getElementById('modebar').style.display")!="none")
    ck("the stream was stopped",
       pg.evaluate("()=>{const v=document.getElementById('vid');return !v.srcObject || v.srcObject.getTracks().every(t=>t.readyState==='ended');}"))

    print("\n[7] nothing threw at any point")
    ck("no page errors across the whole run", not errs, errs)
    b.close()

print("\n%d passed, %d failed"%(passes[0],len(fails)))
for f in fails: print("  FAILED:",f)
raise SystemExit(1 if fails else 0)
