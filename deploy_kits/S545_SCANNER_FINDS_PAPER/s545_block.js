  /* ---- S545 (F-890): the paper found by its colour, and the page turned upright -------------------------
     Steps 1 and 2 above refuse a bill that a hand holds (the fingers break its outline into 5-10 corners) or
     that touches the frame. Step 3: paper is bright and has almost no colour; skin, wood, trays have colour,
     keyboards are dark. The largest such region that carries print (a blank wall never does), its hull, and four
     corners that keep at least 97 % of it -- else a box round it. */
  var CV_PAPER_SAT = 70;
  function quadFromPaper(src, w, h){
    var rgb = null, hsv = null, mv = null, sM = null, vM = null, m = null, k1 = null, k2 = null, cs = null, hier = null, hull = null, ap = null, chS = null, chV = null, ct = null,
        mo = null, hm = null, hv = null, an = null;
    try {
      rgb = new CV.Mat(); hsv = new CV.Mat(); mv = new CV.MatVector();
      CV.cvtColor(src, rgb, CV.COLOR_RGBA2RGB); CV.cvtColor(rgb, hsv, CV.COLOR_RGB2HSV); CV.split(hsv, mv);
      chS = mv.get(1); chV = mv.get(2);                                                // fetched once, released below (the live outline runs every 0.3 s)
      sM = new CV.Mat(); vM = new CV.Mat(); m = new CV.Mat();
      CV.threshold(chS, sM, CV_PAPER_SAT, 255, CV.THRESH_BINARY_INV);          // little colour
      // the bright side of the colourless pixels; on a light table that side holds the table too, so split
      // it once more: paper is the brightest large thing in the frame
      var V = chV.data, S = sM.data, n = w * h, hist = new Array(256).fill(0), i, cnt = 0;
      for (i = 0; i < n; i++) if (S[i]) { hist[V[i]]++; cnt++; }
      var t = otsuRange(hist, 0, 255), above = 0;
      for (i = t + 1; i < 256; i++) above += hist[i];
      if (above > 0.75 * n) t = otsuRange(hist, t + 1, 255);
      CV.threshold(chV, vM, t, 255, CV.THRESH_BINARY);
      CV.bitwise_and(sM, vM, m);
      k1 = CV.Mat.ones(3, 3, CV.CV_8U);
      var r = Math.max(5, Math.round(0.025 * Math.min(w, h))); if (r % 2 === 0) r += 1;
      k2 = CV.Mat.ones(r, r, CV.CV_8U);
      CV.morphologyEx(m, m, CV.MORPH_OPEN, k1);
      mo = m.clone();                                                                   // before the close: the print still shows as holes
      CV.morphologyEx(m, m, CV.MORPH_CLOSE, k2);                                     // the print inside the paper closed
      cs = new CV.MatVector(); hier = new CV.Mat();
      CV.findContours(m, cs, hier, CV.RETR_EXTERNAL, CV.CHAIN_APPROX_SIMPLE);
      var order = [], i;
      for (i = 0; i < cs.size(); i++) { ct = cs.get(i); var a = CV.contourArea(ct); ct.delete(); ct = null;
        if (a >= 0.10 * w * h && a <= 0.985 * w * h) order.push([a, i]); }
      order.sort(function(x, y){ return y[0] - x[0]; });
      // a paper carries print: a bright, colourless region with no print on it (a wall, a cabinet, a white board) is never the paper
      for (var c = 0; c < order.length && c < 5; c++) {
        hull = new CV.Mat(); ct = cs.get(order[c][1]); CV.convexHull(ct, hull, false, true); ct.delete(); ct = null;
        hm = CV.Mat.zeros(h, w, CV.CV_8U); hv = new CV.MatVector(); hv.push_back(hull);
        CV.fillPoly(hm, hv, new CV.Scalar(255)); hv.delete(); hv = null;
        an = new CV.Mat(); CV.bitwise_and(mo, hm, an);
        var inHull = CV.countNonZero(hm), ink = inHull ? 1 - CV.countNonZero(an) / inHull : 0;
        an.delete(); an = null; hm.delete(); hm = null;
        var q = null;
        if (ink >= 0.005 && ink <= 0.5) {
          var ha = CV.contourArea(hull), peri = CV.arcLength(hull, true);
          for (var e = 0.02; e <= 0.121 && !q; e += 0.01) {
            ap = new CV.Mat(); CV.approxPolyDP(hull, ap, e * peri, true);
            if (ap.rows === 4 && CV.isContourConvex(ap) && CV.contourArea(ap) >= 0.97 * ha) {
              var pts = []; for (var j = 0; j < 4; j++) pts.push([ap.data32S[j*2], ap.data32S[j*2+1]]);
              q = orderQuad(pts);
            }
            ap.delete(); ap = null;
          }
          if (!q) {                                                                     // a box round the hull: never cuts the paper
            var bp = CV.RotatedRect.points(CV.minAreaRect(hull));
            q = orderQuad(bp.map(function(pp){ return [Math.max(0, Math.min(w, pp.x)), Math.max(0, Math.min(h, pp.y))]; }));
          }
          if (!(paperQuadOK(q, w, h) && edgesSharp(chV, q, w, h))) q = null;
        }
        hull.delete(); hull = null;
        if (q) return q;
      }
      return null;
    } catch (e) { return null; }
    finally { [rgb, hsv, mv, sM, vM, m, k1, k2, cs, hier, hull, ap, chS, chV, ct, mo, hm, hv, an].forEach(function(x){ try { if (x) x.delete(); } catch (e2) {} }); }
  }
  function edgesSharp(vm, q, w, h){
    /* a paper's edge is a sharp step in brightness; a shadow or uneven light fades over a long way.
       Every side that does not lie along the frame's border must show a clear step (median of 24 samples). */
    var V = vm.data, mg = 0.02 * Math.min(w, h), d = 4, checked = 0;
    var cx = (q[0][0] + q[1][0] + q[2][0] + q[3][0]) / 4, cy = (q[0][1] + q[1][1] + q[2][1] + q[3][1]) / 4;
    var at = function(x, y){ x = Math.max(0, Math.min(w - 1, Math.round(x))); y = Math.max(0, Math.min(h - 1, Math.round(y))); return V[y * w + x]; };
    var onBorder = function(a, b){
      return (a[0] < mg && b[0] < mg) || (a[1] < mg && b[1] < mg) || (a[0] > w - mg && b[0] > w - mg) || (a[1] > h - mg && b[1] > h - mg);
    };
    for (var s = 0; s < 4; s++) {
      var a = q[s], b = q[(s + 1) % 4];
      if (onBorder(a, b)) continue;
      var dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy) || 1, nx = -dy / L, ny = dx / L;
      var mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2;
      if ((cx - mx) * nx + (cy - my) * ny < 0) { nx = -nx; ny = -ny; }              // the normal points inside
      var steps = [];
      for (var k = 1; k <= 24; k++) {
        var f = 0.1 + 0.8 * k / 25, px = a[0] + dx * f, py = a[1] + dy * f;
        steps.push(at(px + nx * d, py + ny * d) - at(px - nx * d, py - ny * d));
      }
      steps.sort(function(x, y){ return x - y; });
      if (steps[12] < 12) return false;
      checked++;
    }
    return checked > 0;
  }
  function otsuRange(hist, lo, hi){
    /* Otsu's threshold over hist[lo..hi]; returns lo when that range is empty */
    var tot = 0, sum = 0, i;
    for (i = lo; i <= hi; i++) { tot += hist[i]; sum += i * hist[i]; }
    if (!tot) return lo;
    var wB = 0, sB = 0, best = -1, bt = lo;
    for (i = lo; i <= hi; i++) {
      wB += hist[i]; if (!wB) continue;
      var wF = tot - wB; if (!wF) break;
      sB += i * hist[i];
      var mB = sB / wB, mF = (sum - sB) / wF, v = wB * wF * (mB - mF) * (mB - mF);
      if (v > best) { best = v; bt = i; }
    }
    return bt;
  }
  function paperQuadOK(q, w, h){
    /* quadOK's size and shape, but a paper may touch the frame's edges; refused only when it IS the frame
       (three or more corners on the frame's own corners) */
    var side = function(a, b){ return Math.hypot(a[0] - b[0], a[1] - b[1]); };
    var top = side(q[0], q[1]), right = side(q[1], q[2]), bot = side(q[2], q[3]), left = side(q[3], q[0]);
    var mn = Math.min(w, h);
    if (Math.min(top, right, bot, left) < 0.12 * mn) return false;
    var ar = ((top + bot) / 2) / ((left + right) / 2);
    if (ar < 0.38 || ar > 2.7) return false;
    var area = Math.abs((q[0][0]*q[1][1] - q[1][0]*q[0][1]) + (q[1][0]*q[2][1] - q[2][0]*q[1][1]) +
                        (q[2][0]*q[3][1] - q[3][0]*q[2][1]) + (q[3][0]*q[0][1] - q[0][0]*q[3][1])) / 2;
    var frac = area / (w * h);
    if (frac < 0.10 || frac > 0.985) return false;
    var onCorner = 0, mg = 0.03 * mn, fc = [[0, 0], [w, 0], [w, h], [0, h]];
    q.forEach(function(p, i){ if (Math.abs(p[0] - fc[i][0]) < mg && Math.abs(p[1] - fc[i][1]) < mg) onCorner++; });
    return onCorner < 3;
  }
  function cvUpright(page){
    /* A wide bill shot with the phone upright comes out sideways. Lines of print make the row profile
       ripple; when the column profile ripples clearly more, the print runs up the page: turn it a quarter. */
    var g = null, sm = null, b = null, rp = null, cp = null, out = null, srcM = null;
    try {
      var s = Math.min(1, 600 / Math.max(page.width, page.height));
      var c = document.createElement("canvas"); c.width = Math.max(32, Math.round(page.width * s)); c.height = Math.max(32, Math.round(page.height * s));
      c.getContext("2d").drawImage(page, 0, 0, c.width, c.height);
      sm = CV.imread(c); g = new CV.Mat(); b = new CV.Mat();
      CV.cvtColor(sm, g, CV.COLOR_RGBA2GRAY);
      CV.threshold(g, b, 0, 1, CV.THRESH_BINARY_INV + CV.THRESH_OTSU);                 // ink = 1
      var W = b.cols, H = b.rows, ink = CV.countNonZero(b) / (W * H);
      if (ink < 0.01 || ink > 0.35) return page;
      rp = new CV.Mat(); cp = new CV.Mat();
      CV.reduce(b, rp, 1, CV.REDUCE_SUM, CV.CV_32F);                                   // one value per row
      CV.reduce(b, cp, 0, CV.REDUCE_SUM, CV.CV_32F);                                   // one value per column
      var ripple = function(arr, n, x0, x1){                                           // mean |step| of the profile, inner 80 %
        var t = 0, cnt = 0, mean = 0, i;
        for (i = x0; i < x1; i++) mean += arr[i]; mean = mean / Math.max(1, x1 - x0);
        if (mean <= 0) return 0;
        for (i = x0 + 1; i < x1; i++) { t += Math.abs(arr[i] - arr[i - 1]); cnt++; }
        return (t / Math.max(1, cnt)) / mean;
      };
      var r0 = Math.round(H * 0.1), r1 = Math.round(H * 0.9), c0 = Math.round(W * 0.1), c1 = Math.round(W * 0.9);
      var rr = ripple(rp.data32F, H, r0, r1), cr = ripple(cp.data32F, W, c0, c1);
      if (!(cr > 1.6 * rr && cr > 0.15)) return page;                                   // print already runs across: leave it
      // which way: the bill's heading is the heavier end; the left strip becomes the top when turned clockwise
      var lft = 0, rgt = 0, q4 = Math.max(1, Math.round(W / 4));
      for (var i = 0; i < W; i++) { if (i < q4) lft += cp.data32F[i]; else if (i >= W - q4) rgt += cp.data32F[i]; }
      srcM = CV.imread(page); out = new CV.Mat();
      CV.rotate(srcM, out, lft >= rgt ? CV.ROTATE_90_CLOCKWISE : CV.ROTATE_90_COUNTERCLOCKWISE);
      var o = document.createElement("canvas"); o.width = out.cols; o.height = out.rows;
      CV.imshow(o, out);
      return o;
    } catch (e) { return page; }
    finally { [g, sm, b, rp, cp, out, srcM].forEach(function(x){ try { if (x) x.delete(); } catch (e2) {} }); }
  }
  window.__scannerS545 = {version: "S545.1", paper: function(canvas){ var s = null; try { s = CV.imread(canvas); return quadFromPaper(s, canvas.width, canvas.height); } finally { if (s) s.delete(); } },
                          upright: function(c){ return cvUpright(c); }};
  /* ---- end S545 ---------------------------------------------------------------------------------------- */
