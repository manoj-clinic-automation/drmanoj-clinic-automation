// S563 browser walk -- the page side (S559's harness.js shape). Loaded BEFORE the widget: it wraps fetch (an upload is
// recorded and answered with a made-up stamp; nothing leaves the machine), then, after the widget has loaded, runs one scene
// and posts what it saw to the walk's own little server (/result). Made-up photos only (a drawn bill on a drawn desk).
// Scenes: dom / save (each surface, OLD and NEW); G -- a page deleted while an Adjust picture is still loading; H -- a page
// deleted while a later page is under adjustment (the stage button's page number).
(function () {
  var Q = new URLSearchParams(location.search);
  var LOG = { surface: Q.get("s"), scenario: Q.get("sc"), w: Q.get("w"), errs: [], ups: [] };
  window.addEventListener("error", function (e) { LOG.errs.push(String(e.message || e)); });
  var realFetch = window.fetch.bind(window);
  function fnv(s) { var h = 0x811c9dc5; for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; } return h.toString(16) + ":" + s.length; }
  function fnvB(u8) { var h = 0x811c9dc5; for (var i = 0; i < u8.length; i++) { h ^= u8[i]; h = Math.imul(h, 16777619) >>> 0; } return h.toString(16) + ":" + u8.length; }
  var n = 0;
  window.fetch = function (url, opts) {
    url = String(url);
    var cfg = window.SCANNER_CONFIG || {};
    if (url === cfg.uploadUrl) {
      n++;
      var rec = { n: n, fields: {}, files: [] }, waits = [];
      LOG.ups.push(rec);
      if (opts && opts.body && opts.body.forEach) {
        opts.body.forEach(function (v, k) {
          if (typeof v === "string") { rec.fields[k] = (k === "client_token") ? "(a token)" : v; }
          else {
            var f = { k: k, name: v.name, type: v.type, size: v.size };
            rec.files.push(f);
            waits.push(v.arrayBuffer().then(function (b) { f.h = fnvB(new Uint8Array(b)); }));
          }
        });
      }
      return Promise.all(waits).then(function () {
        rec.done = true;
        return new Response(JSON.stringify({ ok: true, stamp: "Z-WALK-" + n, id: n }), { status: 200, headers: { "Content-Type": "application/json" } });
      });
    }
    if (url.indexOf("/x/") === 0) return Promise.resolve(new Response("{}", { status: 200, headers: { "Content-Type": "application/json" } }));
    return realFetch(url, opts);
  };
  function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
  async function until(fn, ms) { var t = Date.now(); while (Date.now() - t < (ms || 90000)) { try { if (fn()) return true; } catch (e) {} await sleep(50); } return false; }
  function $(i) { return document.getElementById(i); }
  function photo(seed) {
    var c = document.createElement("canvas"); c.width = 1224; c.height = 1632;
    var g = c.getContext("2d");
    g.fillStyle = "#4a3426"; g.fillRect(0, 0, c.width, c.height);
    g.save(); g.translate(612, 820); g.rotate((seed === 2 ? -4 : 3) * Math.PI / 180);
    var BW = 820, BH = 1160; g.translate(-BW / 2, -BH / 2);
    g.fillStyle = "#f3f1ea"; g.fillRect(0, 0, BW, BH);
    g.fillStyle = "#222"; g.fillRect(BW * 0.25, BH * 0.04, BW * 0.5, BH * 0.06);
    var s = seed * 7919;
    for (var y = 0.16; y < 0.86; y += 0.034) { var x = 0.06; while (x < 0.9) { s = (s * 16807) % 2147483647; var w = 0.05 + (s / 2147483647) * 0.15; g.fillRect(BW * x, BH * y, BW * Math.min(w, 0.94 - x), BH * 0.011); x += w + 0.03; } }
    g.restore();
    return c;
  }
  function pagesH() { return window.__scannerCV.pages().map(fnv); }
  function post() { return realFetch("/result", { method: "POST", body: JSON.stringify(LOG) }); }
  function ready() { return window.__scannerS523 && window.__scannerS523.ready(); }
  function cvState() { return window.__scannerCV.state(); }
  function del(k) { document.querySelectorAll('#pages button[title="Delete this page"]')[k].click(); }
  async function three() {
    window.__scannerCV.add(photo(1)); await until(function () { return window.__scannerCV.pages().length === 1; });
    window.__scannerCV.add(photo(2)); await until(function () { return window.__scannerCV.pages().length === 2; });
    window.__scannerCV.add(photo(3)); await until(function () { return window.__scannerCV.pages().length === 3; });
    var hh = pagesH(); LOG.p1 = hh[0]; LOG.p2 = hh[1]; LOG.p3 = hh[2];
  }
  function pdfStub() {                                  // a stand-in PDF maker: records each page put into the saved paper
    var real = window.jspdf; LOG.pdf = [];
    window.jspdf = { jsPDF: function () { return { addPage: function () {}, addImage: function (du) { LOG.pdf.push(fnv(du)); },
                                                   output: function () { return new Blob(["walk"], { type: "application/pdf" }); } }; } };
    return function () { window.jspdf = real; };
  }

  async function main() {
    var sc = LOG.scenario, cfg = window.SCANNER_CONFIG;
    try {
      if (sc === "dom") {
        if (cfg.cvScan) { LOG.ready = await until(ready); } else { await sleep(600); }
        LOG.dom = fnv($("scanroot").innerHTML); LOG.on = window.__scannerS523 ? window.__scannerS523.on : null;
        LOG.s559 = window.__scannerS559 ? window.__scannerS559.version : null;
      } else if (sc === "save") {                       // a surface's own path: a photo chosen, the corners, Add, Save
        var blob = await new Promise(function (r) { photo(1).toBlob(r, "image/jpeg", 0.9); });
        var dt = new DataTransfer(); dt.items.add(new File([blob], "walk_photo.jpg", { type: "image/jpeg" }));
        $("cam").files = dt.files; $("cam").dispatchEvent(new Event("change"));
        LOG.stage = await until(function () { return $("stage").style.display === "block"; }, 20000);
        $("addpage").click();
        LOG.page = await until(function () { return window.__scannerCV.pages().length === 1; }, 20000);
        LOG.pageh = pagesH()[0];
        $("savebtn").click();
        await until(function () { return LOG.ups.length === 1 && LOG.ups[0].done; }, 20000);
        await sleep(400);
        LOG.hash = location.hash;
      } else {
        LOG.ready = await until(ready);
        if (!LOG.ready) throw new Error("OpenCV did not become ready");
        await three();
        if (sc === "G") {                               // S559-K2-N7: page 1 deleted while page 2's Adjust picture is still loading
          var RealImage = window.Image, srcD = Object.getOwnPropertyDescriptor(HTMLImageElement.prototype, "src");
          window.Image = function () {                  // a slow phone: this one picture starts loading 700 ms late
            var im = new RealImage();
            Object.defineProperty(im, "src", { configurable: true, get: function () { return srcD.get.call(im); },
              set: function (v) { setTimeout(function () { srcD.set.call(im, v); }, 700); } });
            return im;
          };
          window.__scannerCV.adjustOpen(1);
          window.Image = RealImage;
          await sleep(100);
          LOG.adjBefore = cvState().adjust;             // -1: the picture has not loaded yet
          del(0); await sleep(1500);                    // page 1 deleted; the late picture lands after it
          LOG.adjAfter = cvState().adjust; LOG.stage = $("stage").style.display; LOG.label = $("addpage").textContent; LOG.left = pagesH().length;
          $("addpage").click(); await sleep(500);       // her next tap on the stage's button ("Theek hai" when the stage is open)
          var back = pdfStub();
          $("camsave").click(); await sleep(900);
          back();
          LOG.u1 = LOG.ups.length; LOG.stage2 = $("stage").style.display;
        } else if (sc === "H") {                        // the stage button after a delete shifts the page under adjustment
          window.__scannerCV.adjustOpen(2);
          await until(function () { return cvState().adjust === 2; });
          LOG.label0 = $("addpage").textContent;
          del(0); await sleep(300);
          LOG.adj = cvState().adjust; LOG.label = $("addpage").textContent; LOG.stage = $("stage").style.display;
          $("resetcorners").click(); await sleep(150);
          $("addpage").click(); await until(function () { return cvState().adjust === -1; }, 5000);
          var back2 = pdfStub();
          $("camsave").click(); await sleep(900);
          back2();
          LOG.u1 = LOG.ups.length;
        }
      }
    } catch (e) { LOG.errs.push("walk: " + (e && e.message ? e.message : String(e))); }
    LOG.upsSummary = LOG.ups.map(function (u) { return { fields: u.fields, files: u.files }; });
    await post();
  }
  window.addEventListener("load", function () { setTimeout(main, 50); });
})();
