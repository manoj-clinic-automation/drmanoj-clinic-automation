  /* ======================= S523: THE SMART OUTLINE (OpenCV.js), OPT-IN ==========
     Nothing below runs unless the host sets cvScan:true AND cvUrl. Only the bill
     intake does (behind the owner's switch scan.cv on /scanapp/admin); the asset
     pages, Casepack and the five finance scan surfaces never set it, so for them
     this file behaves exactly as before, byte for byte in effect.

     WHY (F-842, measured on the 11-Oct backup): the light outline finder above
     found no outline on 33 of the last 40 real scans -- the whole photo, desk and
     all, went into the PDF -- and every photo was shrunk to 1400 px before it was
     looked at, so no PDF ever carried the camera's resolution.

     WHAT THIS DOES, when the library has arrived on this phone:
       * the camera is asked for 8 MP instead of 2.7 MP (openCam);
       * a live outline is drawn on the camera preview while aiming;
       * each capture is read at full size: the paper found as a true four-cornered
         shape (edges, then a brightness fallback), straightened by perspective,
         kept up to 2400 px on its long side, the B&W flattening done the same way
         as enhanceGray but in the library (fast at this size);
       * the original photo of every page is kept until Save, so a page can be
         ADJUSTED: the existing corner handles open on it, "Theek hai" re-warps;
       * a phone that cannot carry it (deviceMemory < 2 GB, Data Saver on, or the
         download never arrives) keeps the path above unchanged -- autoAddCV hands
         straight to autoAdd.
     The library is served by our own app (cvUrl), cached once per phone. */
  var CV = null, cvReady = false, cvWhy = "", pageSrc = [], pageCorners = [], adjustIdx = -1, adjustImg = null, adjustScale = 1;
  var CV_MAX_IN = 3300, CV_MAX_OUT = 2400, CV_DETECT = 640, CV_LIVE = 360;
  window.__scannerS523 = {version: "S523.1", on: cvScanOn, ready: function(){ return cvReady; }, why: function(){ return cvWhy; }};
  function cvLoad(){
    if (!cvScanOn) return;
    try {
      var mem = navigator.deviceMemory;
      if (mem && mem < 2) { cvWhy = "memory"; return; }
      var con = navigator.connection || {};
      if (con.saveData) { cvWhy = "saveData"; return; }
    } catch (e) {}
    var s = document.createElement("script"); s.async = true; s.src = CFG.cvUrl;
    s.onload = function(){
      var tries = 0;
      (function wait(){
        var c = window.cv;
        if (c && c.Mat) { cvReadyNow(); return; }
        if (c && typeof c.then === "function") { c.then(function(){ cvReadyNow(); }, function(){ cvWhy = "init"; }); return; }
        if (++tries < 300) setTimeout(wait, 100); else cvWhy = "init";
      })();
    };
    s.onerror = function(){ cvWhy = "download"; };
    document.head.appendChild(s);
  }
  function cvReadyNow(){
    if (cvReady) return;
    if (!(window.cv && window.cv.Mat)) { cvWhy = "init"; return; }
    CV = window.cv; cvReady = true; cvWhy = "";
    renderPages();
    if (stream) liveStart();
    var h = $("hint"); if (h && autoPage) h.textContent = "Har photo ek page hai — kaagaz ka outline khud banega; bill ke saare page kheencho, phir Save.";
  }
  function orderQuad(pts){                     // TL, TR, BR, BL by sum / difference
    var s = pts.slice().sort(function(a, b){ return (a[0] + a[1]) - (b[0] + b[1]); });
    var tl = s[0], br = s[3];
    var d = pts.slice().sort(function(a, b){ return (a[0] - a[1]) - (b[0] - b[1]); });
    var bl = d[0], tr = d[3];
    return [tl, tr, br, bl];
  }
  function quadOK(q, w, h){
    var side = function(a, b){ return Math.hypot(a[0] - b[0], a[1] - b[1]); };
    var top = side(q[0], q[1]), right = side(q[1], q[2]), bot = side(q[2], q[3]), left = side(q[3], q[0]);
    var mn = Math.min(w, h);
    if (Math.min(top, right, bot, left) < 0.12 * mn) return false;
    var ar = ((top + bot) / 2) / ((left + right) / 2);
    if (ar < 0.38 || ar > 2.7) return false;
    var area = Math.abs((q[0][0]*q[1][1] - q[1][0]*q[0][1]) + (q[1][0]*q[2][1] - q[2][0]*q[1][1]) +
                        (q[2][0]*q[3][1] - q[3][0]*q[2][1]) + (q[3][0]*q[0][1] - q[0][0]*q[3][1])) / 2;
    var frac = area / (w * h);
    if (frac < 0.10 || frac > 0.90) return false;
    // a box that hugs the frame is the frame, not a paper: three corners within 1.5% of the border = refused
    var hug = 0, m = 0.015 * mn;
    q.forEach(function(p){ if (p[0] < m || p[1] < m || p[0] > w - m || p[1] > h - m) hug++; });
    return hug < 3;
  }
  function brightInside(gray, q, w, h){
    /* paper is brighter than what lies just outside it: the mean inside the quad minus the mean of a ring round it */
    var mask = null, ring = null, k = null, inside = null, out = null;
    try {
      mask = CV.Mat.zeros(h, w, CV.CV_8U);
      var pts = CV.matFromArray(4, 1, CV.CV_32SC1 ? CV.CV_32SC2 : CV.CV_32SC2, [Math.round(q[0][0]), Math.round(q[0][1]), Math.round(q[1][0]), Math.round(q[1][1]),
                                                   Math.round(q[2][0]), Math.round(q[2][1]), Math.round(q[3][0]), Math.round(q[3][1])]);
      var pv = new CV.MatVector(); pv.push_back(pts);
      CV.fillPoly(mask, pv, new CV.Scalar(255));
      pv.delete(); pts.delete();
      var r = Math.max(6, Math.round(0.04 * Math.min(w, h)));
      k = CV.Mat.ones(r, r, CV.CV_8U); ring = new CV.Mat();
      CV.dilate(mask, ring, k);
      CV.subtract(ring, mask, ring);
      inside = CV.mean(gray, mask); out = CV.mean(gray, ring);
      return inside[0] - out[0];
    } catch (e) { return 0; }
    finally { [mask, ring, k].forEach(function(m){ try { if (m) m.delete(); } catch (e2) {} }); }
  }
  function quadFromContours(cs, w, h, eps, gray){
    /* every convex four-cornered contour that could be a paper; the brightest-inside one wins, size as the tie-break */
    var cands = [], i;
    for (i = 0; i < cs.size(); i++) {
      var c = cs.get(i), a = CV.contourArea(c);
      if (a < 0.10 * w * h || a > 0.90 * w * h) { continue; }
      var peri = CV.arcLength(c, true), ap = new CV.Mat();
      CV.approxPolyDP(c, ap, eps * peri, true);
      if (ap.rows === 4 && CV.isContourConvex(ap)) {
        var pts = []; for (var j = 0; j < 4; j++) pts.push([ap.data32S[j*2], ap.data32S[j*2+1]]);
        var q = orderQuad(pts);
        if (quadOK(q, w, h)) cands.push({q: q, a: a, b: gray ? brightInside(gray, q, w, h) : 0});
      }
      ap.delete();
    }
    if (!cands.length) return null;
    var lit = cands.filter(function(c){ return c.b >= 12; });        // clearly brighter inside: a paper on a desk
    var pool = lit.length ? lit : cands;
    pool.sort(function(x, y){ return (y.a - x.a); });
    return pool[0].q;
  }
  function cvFindQuad(canvas, maxSide){
    /* The paper's four corners in the canvas's own coordinates, or null (never a guess). */
    if (!cvReady) return null;
    var sc = Math.min(1, (maxSide || CV_DETECT) / Math.max(canvas.width, canvas.height));
    var w = Math.max(32, Math.round(canvas.width * sc)), h = Math.max(32, Math.round(canvas.height * sc));
    var sm = document.createElement("canvas"); sm.width = w; sm.height = h;
    sm.getContext("2d").drawImage(canvas, 0, 0, w, h);
    var src = null, gray = null, blur = null, edges = null, k = null, cs = null, hier = null, th = null, found = null;
    try {
      src = CV.imread(sm); gray = new CV.Mat(); blur = new CV.Mat(); edges = new CV.Mat(); cs = new CV.MatVector(); hier = new CV.Mat();
      CV.cvtColor(src, gray, CV.COLOR_RGBA2GRAY);
      CV.GaussianBlur(gray, blur, new CV.Size(5, 5), 0);
      // 1. edges: the border of a sheet is the longest clean edge in the frame
      CV.Canny(blur, edges, 40, 120);
      k = CV.Mat.ones(3, 3, CV.CV_8U);
      CV.dilate(edges, edges, k);
      CV.findContours(edges, cs, hier, CV.RETR_LIST, CV.CHAIN_APPROX_SIMPLE);
      found = quadFromContours(cs, w, h, 0.03, blur);
      if (!found) {
        // 2. brightness: paper is the brightest large thing on a desk (Otsu), its hull a quad
        th = new CV.Mat(); CV.threshold(blur, th, 0, 255, CV.THRESH_BINARY + CV.THRESH_OTSU);
        CV.morphologyEx(th, th, CV.MORPH_CLOSE, k);
        cs.delete(); cs = new CV.MatVector();
        CV.findContours(th, cs, hier, CV.RETR_EXTERNAL, CV.CHAIN_APPROX_SIMPLE);
        var hulls = new CV.MatVector();
        for (var i = 0; i < cs.size(); i++) { var hu = new CV.Mat(); CV.convexHull(cs.get(i), hu, false, true); hulls.push_back(hu); hu.delete(); }
        found = quadFromContours(hulls, w, h, 0.04, blur) || quadFromContours(hulls, w, h, 0.08, blur);
        hulls.delete();
      }
    } catch (e) { found = null; }
    finally { [src, gray, blur, edges, k, cs, hier, th].forEach(function(m){ try { if (m) m.delete(); } catch (e2) {} }); }
    if (!found) return null;
    return found.map(function(p){ return [p[0] / sc, p[1] / sc]; });
  }
  function cvWarp(canvas, q, bw){
    /* canvas: the photo at full size; q: four corners in its coordinates. Returns a canvas up to CV_MAX_OUT. */
    var side = function(a, b){ return Math.hypot(a[0] - b[0], a[1] - b[1]); };
    var W = Math.round((side(q[0], q[1]) + side(q[3], q[2])) / 2), H = Math.round((side(q[0], q[3]) + side(q[1], q[2])) / 2);
    var s = Math.min(1, CV_MAX_OUT / Math.max(W, H)); W = Math.max(50, Math.round(W * s)); H = Math.max(50, Math.round(H * s));
    var out = document.createElement("canvas"); out.width = W; out.height = H;
    var src = null, dst = null, M = null, a = null, b = null, g = null, mean = null, f = null, m2 = null;
    try {
      src = CV.imread(canvas); dst = new CV.Mat();
      a = CV.matFromArray(4, 1, CV.CV_32FC2, [q[0][0], q[0][1], q[1][0], q[1][1], q[2][0], q[2][1], q[3][0], q[3][1]]);
      b = CV.matFromArray(4, 1, CV.CV_32FC2, [0, 0, W, 0, W, H, 0, H]);
      M = CV.getPerspectiveTransform(a, b);
      CV.warpPerspective(src, dst, M, new CV.Size(W, H), CV.INTER_LINEAR, CV.BORDER_CONSTANT, new CV.Scalar(255, 255, 255, 255));
      if (bw) {
        // the same arithmetic as enhanceGray above: gray / local mean * 200, capped at 255, then a min-max stretch
        g = new CV.Mat(); CV.cvtColor(dst, g, CV.COLOR_RGBA2GRAY);
        var ks = Math.max(15, Math.floor(Math.min(W, H) / 8)); if (ks % 2 === 0) ks += 1;
        mean = new CV.Mat(); CV.blur(g, mean, new CV.Size(ks, ks));
        f = new CV.Mat(); m2 = new CV.Mat();
        g.convertTo(f, CV.CV_32F); mean.convertTo(m2, CV.CV_32F, 1, 1);          // +1: never divide by zero
        CV.divide(f, m2, f, 200);
        CV.threshold(f, f, 255, 255, CV.THRESH_TRUNC);
        CV.normalize(f, f, 0, 255, CV.NORM_MINMAX);
        f.convertTo(g, CV.CV_8U);
        CV.imshow(out, g);
      } else {
        CV.imshow(out, dst);
      }
    } finally { [src, dst, M, a, b, g, mean, f, m2].forEach(function(m){ try { if (m) m.delete(); } catch (e2) {} }); }
    return out;
  }
  function fullCanvas(img){
    var s = Math.min(1, CV_MAX_IN / Math.max(img.width, img.height));
    var c = document.createElement("canvas"); c.width = Math.round(img.width * s); c.height = Math.round(img.height * s);
    c.getContext("2d").drawImage(img, 0, 0, c.width, c.height);
    return c;
  }
  function autoAddCV(src){
    /* src: a canvas (from the camera) or an image URL (a chosen photo). */
    if (!cvReady) {                                                   // the library is not here: the S441 path, unchanged
      autoAdd(typeof src === "string" ? src : src.toDataURL("image/jpeg", 0.92)); return;
    }
    var go = function(full){
      var q = cvFindQuad(full), du, n, whole = false;
      if (!q) {
        // the light finder as the second opinion, on a 1400-px copy, as autoAdd does
        var s = Math.min(1, 1400 / Math.max(full.width, full.height));
        var c2 = document.createElement("canvas"); c2.width = Math.round(full.width * s); c2.height = Math.round(full.height * s);
        c2.getContext("2d").drawImage(full, 0, 0, c2.width, c2.height);
        var f2 = autoDetect(c2);
        if (f2) q = f2.map(function(p){ return [p[0] / s, p[1] / s]; });
      }
      if (!q) { q = [[0, 0], [full.width, 0], [full.width, full.height], [0, full.height]]; whole = true; }
      try { du = cvWarp(full, q, $("bw").checked).toDataURL("image/jpeg", 0.88); }
      catch (e) { autoAdd(full.toDataURL("image/jpeg", 0.92)); return; }
      var orig = full.toDataURL("image/jpeg", 0.92);
      if (retakeIdx >= 0 && retakeIdx < pages.length) { pages[retakeIdx] = du; pageSrc[retakeIdx] = orig; pageCorners[retakeIdx] = q; n = retakeIdx + 1; retakeIdx = -1; }
      else { pages.push(du); pageSrc.push(orig); pageCorners.push(q); n = pages.length; }
      renderPages(); updateSaveBar();
      say("Page " + n + " ✓" + (whole ? " (poori photo — Adjust se kaato)" : ""));
      if (importQueue.length) setTimeout(loadNextImport, 60); else $("cam").value = "";
    };
    if (typeof src === "string") {
      var img = new Image();
      img.onload = function(){ go(fullCanvas(img)); };
      img.onerror = function(){ say("Could not read that image."); if (importQueue.length) setTimeout(loadNextImport, 60); };
      img.src = src;
    } else { go(fullCanvas(src)); }
  }
  function dropSrc(i){ pageSrc.splice(i, 1); pageCorners.splice(i, 1); if (adjustIdx === i) adjustIdx = -1; }
  function clearSrc(){ pageSrc = []; pageCorners = []; adjustIdx = -1; adjustImg = null; }
  function adjustOpen(i){
    if (!cvReady || !pageSrc[i]) return;
    var img = new Image();
    img.onload = function(){
      adjustIdx = i; adjustImg = img; retakeIdx = -1;
      var s = Math.min(1, 1400 / Math.max(img.width, img.height)); adjustScale = s;
      cv.width = ov.width = Math.round(img.width * s); cv.height = ov.height = Math.round(img.height * s);
      ctx.drawImage(img, 0, 0, cv.width, cv.height); srcImg = img;
      var q = pageCorners[i];
      if (q) corners = q.map(function(p){ return clampPt([p[0] * s, p[1] * s]); });
      else { var mx = cv.width * 0.08, my = cv.height * 0.08; corners = [[mx, my], [cv.width - mx, my], [cv.width - mx, cv.height - my], [mx, cv.height - my]]; }
      $("addpage").textContent = "✔ Theek hai — page " + (i + 1);
      $("stage").style.display = "block"; drawOverlay(); renderPages();
      $("stage").scrollIntoView({behavior: "smooth", block: "nearest"});
      say("Page " + (i + 1) + ": kone kheench kar kaagaz par lagao, phir Theek hai.");
    };
    img.onerror = function(){ say("Could not open that page again."); };
    img.src = pageSrc[i];
  }
  function adjustDone(){
    var i = adjustIdx; if (i < 0 || !adjustImg) { adjustIdx = -1; return; }
    var full = fullCanvas(adjustImg), k = 1 / adjustScale;
    var fs = Math.min(1, CV_MAX_IN / Math.max(adjustImg.width, adjustImg.height));   // fullCanvas may have shrunk it
    var q = corners.map(function(p){ return [Math.max(0, Math.min(full.width, p[0] * k * fs)), Math.max(0, Math.min(full.height, p[1] * k * fs))]; });
    try { pages[i] = cvWarp(full, q, $("bw").checked).toDataURL("image/jpeg", 0.88); pageCorners[i] = q; }
    catch (e) { say("Could not cut that page (" + (e && e.message ? e.message : "error") + ")."); }
    adjustIdx = -1; adjustImg = null; $("addpage").textContent = "✔ Add this page";
    $("stage").style.display = "none"; renderPages(); updateSaveBar();
    say("Page " + (i + 1) + " theek ✓");
  }
  // ---- the live outline on the camera preview
  var liveT = null, liveC = null, liveBusy = false;
  function liveStart(){
    if (!cvScanOn || !cvReady || liveT) return;
    var wrap = $("camwrap"), v = $("vid"); if (!wrap || !v) return;
    wrap.style.position = "relative";
    if (!liveC) { liveC = document.createElement("canvas"); liveC.id = "livov";
      liveC.style.cssText = "position:absolute;pointer-events:none;left:0;top:0"; wrap.appendChild(liveC); }
    liveC.style.display = "block";
    liveT = setInterval(liveTick, 300);
  }
  function liveStop(){ if (liveT) { clearInterval(liveT); liveT = null; } if (liveC) { liveC.style.display = "none"; } }
  function liveTick(){
    if (liveBusy || !stream) return;
    var v = $("vid"); if (!v || !v.videoWidth) return;
    liveBusy = true;
    try {
      var r = v.getBoundingClientRect(), wr = $("camwrap").getBoundingClientRect();
      liveC.style.left = (r.left - wr.left) + "px"; liveC.style.top = (r.top - wr.top) + "px";
      liveC.style.width = r.width + "px"; liveC.style.height = r.height + "px";
      if (liveC.width !== Math.round(r.width) || liveC.height !== Math.round(r.height)) { liveC.width = Math.round(r.width); liveC.height = Math.round(r.height); }
      var sc = Math.min(1, CV_LIVE / Math.max(v.videoWidth, v.videoHeight));
      var c = document.createElement("canvas"); c.width = Math.round(v.videoWidth * sc); c.height = Math.round(v.videoHeight * sc);
      c.getContext("2d").drawImage(v, 0, 0, c.width, c.height);
      var q = cvFindQuad(c, CV_LIVE);
      var g = liveC.getContext("2d"); g.clearRect(0, 0, liveC.width, liveC.height);
      if (q) {
        // object-fit:contain -- the frame sits centred inside the element
        var fit = Math.min(r.width / v.videoWidth, r.height / v.videoHeight);
        var ox = (r.width - v.videoWidth * fit) / 2, oy = (r.height - v.videoHeight * fit) / 2, f = fit / sc;
        g.strokeStyle = "#2ecc71"; g.lineWidth = 3; g.beginPath();
        for (var i = 0; i < 5; i++) { var p = q[i % 4]; var x = ox + p[0] * f, y = oy + p[1] * f; if (i) g.lineTo(x, y); else g.moveTo(x, y); }
        g.stroke();
      }
    } catch (e) {}
    liveBusy = false;
  }
  window.__scannerCV = {find: function(canvas, max){ return cvFindQuad(canvas, max); }, warp: function(canvas, q, bw){ return cvWarp(canvas, q, bw); },
                        pages: function(){ return pages.slice(); }, corners: function(){ return pageCorners.slice(); }, add: autoAddCV,
                        adjustOpen: adjustOpen, adjustDone: adjustDone, state: function(){ return {ready: cvReady, why: cvWhy, on: cvScanOn, adjust: adjustIdx}; }};
  cvLoad();
  /* ======================= end S523 ======================================= */
