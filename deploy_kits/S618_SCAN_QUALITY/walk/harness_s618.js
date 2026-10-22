/* harness_s618.js -- S618's browser walk scenes (headless Chrome on the PC). Loaded AFTER the widget by run_browser_walk_s618.py's page.
   Reports one JSON to /result. Made-up uploads only (the little server answers every upload); the bill pictures never leave the PC. */
(function () {
  var Q = new URLSearchParams(location.search), SC = Q.get("sc"), R = {sc: SC, w: Q.get("w"), errs: []};
  window.addEventListener("error", function (e) { R.errs.push(String(e.message || e)); });
  function post() { fetch("/result", {method: "POST", body: JSON.stringify(R)}); }
  function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
  function img(name) { return new Promise(function (res, rej) { var i = new Image(); i.onload = function () { res(i); }; i.onerror = rej; i.src = "/page/" + name; }); }
  function canvasOf(i) { var c = document.createElement("canvas"); c.width = i.width; c.height = i.height; c.getContext("2d").drawImage(i, 0, 0); return c; }
  function desk(i) {            /* the stored page laid on a desk-coloured margin, as a camera frame would show it */
    var m = 0.16, W = Math.round(i.width * (1 + 2 * m)), H = Math.round(i.height * (1 + 2 * m));
    var c = document.createElement("canvas"); c.width = W; c.height = H; var g = c.getContext("2d");
    g.fillStyle = "#6f5238"; g.fillRect(0, 0, W, H);
    for (var k = 0; k < 400; k++) { g.fillStyle = "rgba(" + (90 + (k * 37) % 40) + "," + (66 + (k * 13) % 30) + ",40,0.35)"; g.fillRect((k * 97) % W, (k * 53) % H, 30, 6); }
    g.drawImage(i, Math.round(i.width * m), Math.round(i.height * m));
    return c;
  }
  function state() { return window.__scannerS618 ? window.__scannerS618.state() : null; }
  function npages() { var p = document.querySelectorAll("#pages img"); return p.length; }
  function box() { var b = document.getElementById("blurbox"); return b && b.style.display !== "none" ? b.textContent.replace(/\s+/g, " ").trim() : ""; }
  async function ready() {
    for (var k = 0; k < 600; k++) { if (window.__scannerS523 && window.__scannerS523.ready()) return true; await sleep(100); }
    return false;
  }
  async function add(c) { window.__scannerCV.add(c); for (var k = 0; k < 60; k++) { await sleep(100); } }
  async function ups() { var r = await fetch("/uploads"); return r.json(); }
  async function run() {
    R.ready = await ready();
    R.s618 = window.__scannerS618 ? window.__scannerS618.version : null;
    R.blurMin = (window.SCANNER_CONFIG || {}).blurMin;
    if (!R.ready) { R.errs.push("OpenCV not ready"); return; }
    if (SC === "cal") {
      var names = await (await fetch("/pages.json")).json(); R.cal = {};
      for (var n of names) {
        var i = await img(n), c = canvasOf(i), direct = window.__scannerS618 ? window.__scannerS618.sharp(c) : null, pipe = null, found = null;
        try {
          var d = desk(i), q = window.__scannerCV.find(d);
          found = !!q;
          if (!q) q = [[0, 0], [d.width, 0], [d.width, d.height], [0, d.height]];
          var pg = window.__scannerS545.upright(window.__scannerCV.warp(d, q, true));
          pipe = window.__scannerS618 ? window.__scannerS618.sharp(pg) : null;
        } catch (e) { R.errs.push(n + ": " + e); }
        R.cal[n] = {direct: direct, pipe: pipe, found: found, w: i.width, h: i.height};
      }
    } else if (SC === "refuse" || SC === "keep") {
      var i2 = await img(Q.get("p")); await add(desk(i2));
      R.pages = npages(); R.box = box(); R.state = state();
    } else if (SC === "three") {
      var i3 = await img(Q.get("p")), seq = [];
      for (var t = 0; t < 3; t++) { await add(desk(i3)); seq.push({pages: npages(), box: box(), state: state()}); }
      R.seq = seq;
      var cs = document.getElementById("camsave"); if (cs) cs.click();
      for (var k = 0; k < 80; k++) { await sleep(100); var u = await ups(); if (u.length) break; }
      R.ups = await ups();
    } else if (SC === "gallery") {
      var dt = new DataTransfer(), list = (Q.get("ps") || "").split(","), seen = [];
      for (var nm of list) { var ii = await img(nm), dc = desk(ii); var b = await new Promise(function (r) { dc.toBlob(r, "image/jpeg", 0.92); }); dt.items.add(new File([b], nm, {type: "image/jpeg"})); }
      var inp = document.getElementById("cam"); inp.files = dt.files; inp.dispatchEvent(new Event("change"));
      for (var k2 = 0; k2 < 200; k2++) { await sleep(100); if (box()) seen.push(npages()); if (npages() >= 2 && k2 > 60) break; }
      await sleep(1500);
      R.pages = npages(); R.sawBoxAt = seen.length ? seen[0] : null; R.state = state();
    } else if (SC === "aspect") {
      R.guidehint = !!document.getElementById("guidehint");
      R.cfgAR = (window.SCANNER_CONFIG || {}).expectAspect || null;
      R.arSquare = window.__scannerS618 ? window.__scannerS618.arOK(1000, 1000) : null;
      R.arHalfA4 = window.__scannerS618 ? window.__scannerS618.arOK(705, 1000) : null;
      if (window.SCANNER_CONFIG) { delete window.SCANNER_CONFIG.expectAspect; }                    // the lane button moves to a clinic bill
      R.arSquareAfterClinic = window.__scannerS618 ? window.__scannerS618.arOK(1000, 1000) : null;
    } else if (SC === "intake") {
      var i4 = await img(Q.get("p")), i5 = await img(Q.get("p2"));
      await add(desk(i4)); document.getElementById("camsave").click();
      for (var k3 = 0; k3 < 80; k3++) { await sleep(100); if ((await ups()).length >= 1) break; }
      await sleep(400);
      await add(desk(i5)); document.getElementById("camsave").click();
      for (var k4 = 0; k4 < 80; k4++) { await sleep(100); if ((await ups()).length >= 2) break; }
      R.ups = await ups();
    }
  }
  run().then(post, function (e) { R.errs.push("run: " + e); post(); });
})();
