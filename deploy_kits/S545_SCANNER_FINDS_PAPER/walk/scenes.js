// Made-up photos for the S545 bench. Evaluated inside the page; defines runAll(OLD, NEW).
var FW = 1224, FH = 1632;                       // a portrait camera frame (half of 2448 x 3264)
var rnd = (function(){ var s = 12345; return function(){ s = (s * 16807) % 2147483647; return s / 2147483647; }; })();
function mk(w, h){ var c = document.createElement('canvas'); c.width = w; c.height = h; return c; }
function drawBill(g, BW, BH, o){
  o = o || {};
  g.fillStyle = '#f3f1ea'; g.fillRect(0, 0, BW, BH);
  var ink = '#222';
  g.fillStyle = ink;
  // heading: the heavy end
  g.fillRect(BW * 0.25, BH * 0.04, BW * 0.5, BH * 0.06);
  for (var i = 0; i < 3; i++) g.fillRect(BW * 0.2, BH * (0.12 + i * 0.03), BW * 0.6, BH * 0.012);
  // table rows
  var y0 = 0.25, y1 = 0.80, step = o.dense ? 0.028 : 0.036;
  for (var y = y0; y < y1; y += step) {
    var x = 0.05;
    while (x < 0.93) { var w = 0.04 + rnd() * 0.14; g.fillRect(BW * x, BH * y, BW * Math.min(w, 0.95 - x), BH * 0.011); x += w + 0.03; }
  }
  if (o.rules) {
    g.fillRect(BW * 0.03, BH * 0.22, BW * 0.94, 3); g.fillRect(BW * 0.03, BH * 0.82, BW * 0.94, 3);
    [0.03, 0.12, 0.45, 0.6, 0.75, 0.97].forEach(function(x){ g.fillRect(BW * x, BH * 0.22, 3, BH * 0.6); });
  }
  // footer: a total and a signature
  g.fillRect(BW * 0.65, BH * 0.86, BW * 0.28, BH * 0.015);
  g.fillRect(BW * 0.70, BH * 0.93, BW * 0.18, BH * 0.008);
}
function billCanvas(BW, BH, o){ var c = mk(BW, BH); drawBill(c.getContext('2d'), BW, BH, o); return c; }
function corners(cx, cy, w, h, deg){
  var a = deg * Math.PI / 180, ca = Math.cos(a), sa = Math.sin(a);
  return [[-w/2, -h/2], [w/2, -h/2], [w/2, h/2], [-w/2, h/2]].map(function(p){ return [cx + p[0] * ca - p[1] * sa, cy + p[0] * sa + p[1] * ca]; });
}
function background(g, kind){
  var i;
  if (kind === 'wood') {
    g.fillStyle = '#7a4a24'; g.fillRect(0, 0, FW, FH);
    for (i = 0; i < 160; i++) { g.strokeStyle = rnd() < 0.5 ? '#8b5a2b' : '#6a3d1c'; g.lineWidth = 2 + rnd() * 6; g.beginPath(); var y = rnd() * FH; g.moveTo(0, y); g.bezierCurveTo(FW * 0.3, y + 20 * rnd(), FW * 0.6, y - 20 * rnd(), FW, y + 10); g.stroke(); }
  } else if (kind === 'keyboard') {
    g.fillStyle = '#26272b'; g.fillRect(0, 0, FW, FH);
    for (var y = 20; y < FH; y += 95) for (var x = 15; x < FW; x += 95) { g.fillStyle = '#3a3b40'; g.fillRect(x, y, 80, 80); g.fillStyle = '#bdbdbd'; g.fillRect(x + 30, y + 30, 14, 18); }
  } else if (kind === 'tray') {
    g.fillStyle = '#3d6fb0'; g.fillRect(0, 0, FW, FH);
  } else if (kind === 'wall') {             // a blank bright wall over a dark desk: bigger than the bill, no print on it
    g.fillStyle = '#3a2a20'; g.fillRect(0, 0, FW, FH);
    g.fillStyle = '#efefec'; g.fillRect(0, 0, FW, 720);
  } else if (kind === 'grey') {
    g.fillStyle = '#c4c4c0'; g.fillRect(0, 0, FW, FH);
  }
}
function hand(g, x, y, deg, s){
  g.save(); g.translate(x, y); g.rotate(deg * Math.PI / 180); g.scale(s, s);
  g.fillStyle = '#c98a62';
  g.beginPath(); g.ellipse(0, 170, 130, 150, 0, 0, Math.PI * 2); g.fill();
  [-90, -30, 30, 90].forEach(function(fx, i){ g.beginPath(); g.ellipse(fx, -20 - (i === 1 || i === 2 ? 30 : 0), 30, 130, 0, 0, Math.PI * 2); g.fill(); });
  g.fillStyle = '#b57650'; g.beginPath(); g.ellipse(-150, 120, 32, 110, -0.6, 0, Math.PI * 2); g.fill();   // thumb
  g.restore();
}
function noise(c, amt){
  var g = c.getContext('2d'), d = g.getImageData(0, 0, c.width, c.height), p = d.data;
  for (var i = 0; i < p.length; i += 4) { var n = (rnd() - 0.5) * amt; p[i] += n; p[i+1] += n; p[i+2] += n; }
  g.putImageData(d, 0, 0);
}
function shade(c){             // a soft light from the top-left
  var g = c.getContext('2d'), gr = g.createLinearGradient(0, 0, c.width, c.height);
  gr.addColorStop(0, 'rgba(255,255,255,0.06)'); gr.addColorStop(1, 'rgba(0,0,0,0.18)');
  g.fillStyle = gr; g.fillRect(0, 0, c.width, c.height);
}
function scene(spec){
  var c = mk(FW, FH), g = c.getContext('2d');
  background(g, spec.bg);
  var q = corners(spec.cx, spec.cy, spec.w, spec.h, spec.deg);
  var b = billCanvas(Math.round(spec.bw), Math.round(spec.bh), spec.bill);
  // the bill's own top-left -> q[0], top-right -> q[1], bottom-left -> q[3]
  var BW = b.width, BH = b.height;
  g.save();
  g.setTransform((q[1][0] - q[0][0]) / BW, (q[1][1] - q[0][1]) / BW, (q[3][0] - q[0][0]) / BH, (q[3][1] - q[0][1]) / BH, q[0][0], q[0][1]);
  g.drawImage(b, 0, 0); g.restore();
  (spec.hands || []).forEach(function(h){ hand(g, h[0], h[1], h[2], h[3]); });
  shade(c); noise(c, 14);
  return {canvas: c, truth: q};
}
function polyMask(poly, s){
  var c = mk(Math.round(FW * s), Math.round(FH * s)), g = c.getContext('2d');
  g.fillStyle = '#fff'; g.beginPath(); poly.forEach(function(p, i){ if (i) g.lineTo(p[0] * s, p[1] * s); else g.moveTo(p[0] * s, p[1] * s); }); g.closePath(); g.fill();
  var d = g.getImageData(0, 0, c.width, c.height).data, m = new Uint8Array(c.width * c.height);
  for (var i = 0; i < m.length; i++) m[i] = d[i * 4 + 3] > 127 ? 1 : 0;
  return m;
}
function score(found, truth){
  if (!found) return {iou: 0, cov: 0, found: false};
  var A = polyMask(found, 0.25), B = polyMask(truth, 0.25), inter = 0, uni = 0, tb = 0;
  for (var i = 0; i < A.length; i++) { if (A[i] && B[i]) inter++; if (A[i] || B[i]) uni++; if (B[i]) tb++; }
  return {iou: +(inter / uni).toFixed(3), cov: +(inter / tb).toFixed(3), found: true};
}
var CASES = [
  // name, expect: 'fix' = the old finder fails and the new must pass; 'keep' = both must pass; 'info' = recorded
  {name: 'A sideways bill, hand on its edge, wood desk', expect: 'fix', bg: 'wood', cx: 612, cy: 820, w: 1060, h: 1500 * 0.97, bw: 1500, bh: 1060, deg: 0, rot: 90, hands: [[1080, 900, -80, 1.1]]},
  {name: 'B bill touching both side edges, keyboard, hand below', expect: 'fix', bg: 'keyboard', cx: 612, cy: 760, w: 1224, h: 900, bw: 1500, bh: 1060, deg: 0, hands: [[640, 1280, 0, 1.2]]},
  {name: 'C portrait paper on a desk, no hand', expect: 'keep', bg: 'wood', cx: 612, cy: 816, w: 860, h: 1200, bw: 1060, bh: 1500, deg: 4},
  {name: 'D tilted bill touching the top, two fingers on it, blue tray', expect: 'fix', bg: 'tray', cx: 600, cy: 640, w: 1000, h: 1280, bw: 1060, bh: 1500, deg: -6, hands: [[300, 260, 170, 0.9]]},
  {name: 'E bill held with both hands, wood desk', expect: 'fix', bg: 'wood', cx: 612, cy: 820, w: 1000, h: 1400, bw: 1060, bh: 1500, deg: 2, hands: [[80, 900, 80, 1.0], [1150, 820, -80, 1.0]]},
  {name: 'F bill on a light grey table, hand on it', expect: 'fix', bg: 'grey', cx: 612, cy: 816, w: 900, h: 1260, bw: 1060, bh: 1500, deg: 3, hands: [[1050, 1200, -60, 1.0]]},
  {name: 'H light table, sideways bill touching top and bottom, hand on its side', expect: 'fix', bg: 'grey', cx: 600, cy: 816, w: 1632, h: 1050, bw: 1500, bh: 1060, deg: 0, rot: 90, hands: [[1120, 820, -85, 1.1]]},
  {name: 'I light table, bill touching both sides, fingers at the bottom', expect: 'fix', bg: 'grey', cx: 612, cy: 760, w: 1224, h: 880, bw: 1500, bh: 1060, deg: 0, hands: [[620, 1260, 0, 1.2]]},
  {name: 'J light table, a thumb over one corner', expect: 'info', bg: 'grey', cx: 612, cy: 816, w: 920, h: 1300, bw: 1060, bh: 1500, deg: -2, hands: [[230, 1520, 40, 0.9]]},
  {name: 'K wood desk, sideways bill, fingers over two edges', expect: 'fix', bg: 'wood', cx: 612, cy: 816, w: 1500, h: 1100, bw: 1500, bh: 1060, deg: 0, rot: 90, hands: [[100, 700, 85, 0.9], [1130, 950, -85, 0.9]]},
  {name: 'L a blank bright wall above, the bill on a dark desk with a hand', expect: 'notwall', bg: 'wall', cx: 612, cy: 1190, w: 760, h: 560, bw: 1500, bh: 1060, deg: 2, hands: [[1000, 1300, -70, 0.8]]},
  {name: 'M a blank bright wall above, the bill on a dark desk, no hand', expect: 'notwall', bg: 'wall', cx: 612, cy: 1190, w: 760, h: 560, bw: 1500, bh: 1060, deg: 0},
  {name: 'G paper filling the frame', expect: 'info', bg: 'wood', cx: 612, cy: 816, w: 1214, h: 1622, bw: 1060, bh: 1500, deg: 0}
];
function runAll(OLD, NEW){
  var out = [];
  CASES.forEach(function(k){
    var spec = Object.assign({}, k);
    if (k.rot === 90) {                    // the bill's own width runs down the frame: drawn as a w x h box turned 90 degrees
      spec.w = k.h; spec.h = k.w; spec.deg = 90;
    }
    var sc = scene(spec);
    var t0 = performance.now(), fo = OLD.find(sc.canvas), t1 = performance.now(), fn = NEW.find(sc.canvas), t2 = performance.now();
    var so = score(fo, sc.truth), sn = score(fn, sc.truth);
    var newPass = sn.iou >= 0.88 && sn.cov >= 0.97, oldPass = so.iou >= 0.88 && so.cov >= 0.97;
    var verdict = k.expect === 'fix' ? (newPass && !oldPass ? 'PASS' : (newPass ? 'PASS(old also passed)' : 'FAIL'))
                : k.expect === 'keep' ? (newPass && oldPass ? 'PASS' : 'FAIL')
                : k.expect === 'notwall' ? ((!sn.found || newPass) ? (newPass ? 'PASS (the bill)' : 'PASS (whole photo kept)') : 'FAIL (not the bill)') : 'INFO';
    out.push({case: k.name, old: so, new: sn, ms_old: Math.round(t1 - t0), ms_new: Math.round(t2 - t1), verdict: verdict});
  });
  // step 3 alone (the paper by its colour), at the detection size: on the wall scenes it must give the bill or nothing
  var S3 = [];
  CASES.forEach(function(k){
    if (['notwall', 'fix'].indexOf(k.expect) < 0) return;
    var spec = Object.assign({}, k); if (k.rot === 90) { spec.w = k.h; spec.h = k.w; spec.deg = 90; }
    var sc = scene(spec), f = 640 / FH, sm = mk(Math.round(FW * f), Math.round(FH * f));
    sm.getContext('2d').drawImage(sc.canvas, 0, 0, sm.width, sm.height);
    var q = NEW.paper(sm); q = q ? q.map(function(p){ return [p[0] / f, p[1] / f]; }) : null;
    var s = score(q, sc.truth), ok = (!s.found) || (s.iou >= 0.88 && s.cov >= 0.97);
    S3.push({case: k.name, step3: s, verdict: k.expect === 'notwall' ? (ok ? (s.found ? 'PASS (the bill)' : 'PASS (nothing)') : 'FAIL (not the bill)') : (s.found && ok ? 'PASS' : (s.found ? 'FAIL' : 'INFO (steps 1-2 decide)'))});
  });
  // the upright check
  function gray(c, w, h){ var x = mk(w, h), g = x.getContext('2d'); g.drawImage(c, 0, 0, w, h); var d = g.getImageData(0, 0, w, h).data, a = []; for (var i = 0; i < d.length; i += 4) a.push(d[i]); return a; }
  function rot(c, cw){ var o = mk(c.height, c.width), g = o.getContext('2d'); g.translate(o.width / 2, o.height / 2); g.rotate((cw ? 1 : -1) * Math.PI / 2); g.drawImage(c, -c.width / 2, -c.height / 2); return o; }
  function judge(res, ref){
    if ((res.width > res.height) !== (ref.width > ref.height)) return 'sideways';
    var A = gray(res, 120, 85), B = gray(ref, 120, 85), Bf = B.slice().reverse(), d1 = 0, d2 = 0;
    for (var i = 0; i < A.length; i++) { d1 += Math.abs(A[i] - B[i]); d2 += Math.abs(A[i] - Bf[i]); }
    return d1 <= d2 ? 'upright' : 'upside-down';
  }
  var UP = [];
  var land = billCanvas(1500, 1060), land2 = billCanvas(1500, 1060, {rules: true}), port = billCanvas(1060, 1500), port2 = billCanvas(1060, 1500, {rules: true, dense: true});
  [['U1 landscape bill, upright', land, land, 'upright'], ['U2 landscape bill turned clockwise', rot(land, true), land, 'upright'],
   ['U3 landscape bill turned anticlockwise', rot(land, false), land, 'upright'], ['U4 portrait page, upright', port, port, 'upright'],
   ['U5 ruled table bill, upright', land2, land2, 'upright'], ['U6 ruled dense portrait page, upright', port2, port2, 'upright'],
   ['U7 ruled table bill turned clockwise', rot(land2, true), land2, 'upright']].forEach(function(u){
    var r = NEW.upright(u[1]); var j = judge(r, u[2]);
    UP.push({case: u[0], result: j, verdict: j === 'upright' ? 'PASS' : (j === 'upside-down' && u[0].indexOf('turned') >= 0 ? 'PARTIAL (upside-down)' : 'FAIL')});
  });
  return {find: out, step3: S3, upright: UP};
}
