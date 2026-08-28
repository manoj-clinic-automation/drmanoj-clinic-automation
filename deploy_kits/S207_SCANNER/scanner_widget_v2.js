/* scanner_widget.js — shared document-scanner widget (Stage 1A)
 * ----------------------------------------------------------------------------
 * Reusable across apps (Asset Register now; Casepack next). The host page mounts
 * it by (a) placing <div id=scanroot></div>, (b) setting window.SCANNER_CONFIG,
 * (c) loading jsPDF, then this file. NOTHING app-specific lives here.
 *
 * window.SCANNER_CONFIG = {
 *   title:        "Scan → Office Printer",     // heading
 *   uploadUrl:    "/files/upload",             // where each file POSTs
 *   fileField:    "file",                      // multipart field name for the blob
 *   uploadFields: { entity:"asset", entity_id:"5", sensitive:"1" }, // sent with every file
 *   nameBase:     "Office_Printer",            // sanitised filename stem (date appended)
 *   backUrl:      "/asset/5",                  // where "finish"/"done" returns
 *   allowIdCard:  true, allowBatch: true       // optional feature gates (default true)
 * }
 *
 * Camera / homography-warp / loupe / edge-handle logic is carried VERBATIM from
 * Asset Register v1.2.0. New in 1A: multi-photo import, add-whole-image (no crop),
 * per-page delete, ID-card 2-up, batch (one file each, renamable), editable
 * filename before every save.
 *
 * ===========================================================================
 * v2 (S207, 28-Aug-2026) -- three faults found by scanning a real driving licence.
 * The SCANNER_CONFIG contract above is UNCHANGED; this is a drop-in replacement.
 *
 *   1. NO AUTOCROP. resetCorners() set a fixed 8% inset and that was the whole
 *      of it -- the header of v1 said auto-detect was "Stage 1B and deliberately
 *      NOT here". A licence fills perhaps a third of the frame, so all four
 *      corners had to be dragged a long way, every single time. autoDetect()
 *      below now places the outline on the document. Manual dragging is
 *      untouched and remains the fallback it always was.
 *
 *   2. THE CAMERA HID THE BUTTONS. <video> carried max-width:100% and NO height
 *      limit. Held upright a phone returns a portrait stream, so on a 390px
 *      screen the video rendered ~520px tall; with the heading, three mode
 *      radios, the hint and the open-camera row above it, Capture sat about
 *      700px down -- below the fold, with Save further down still.
 *
 *   3. THE BUTTONS WERE TOO SMALL TO HIT. .btn is ~33px tall and .btn.small
 *      ~22px, against ~44px for a reliable finger. Three of the four buttons in
 *      the stage row were the small variant.
 *
 * Everything below the marked v2 blocks is v1, byte for byte. BASELINE.md5
 * records the file this was cut from.
 * ------------------------------------------------------------------------- */
(function () {
  var CFG = window.SCANNER_CONFIG || {};
  CFG.fileField = CFG.fileField || "file";
  CFG.uploadFields = CFG.uploadFields || {};
  CFG.nameBase = (CFG.nameBase || "scan").toString();
  CFG.backUrl = CFG.backUrl || "/";
  var allowId = CFG.allowIdCard !== false;
  var allowBatch = CFG.allowBatch !== false;

  var root = document.getElementById("scanroot");
  if (!root) { return; }

  /* ============== v2: STYLES, INJECTED SO THE HOST PAGE NEED NOT CHANGE =====
     The widget is shared -- Asset Register today, Casepack next -- so its
     contract must not move. These rules are scoped to #scanroot and override
     the host stylesheet without touching it.

     THE TWO FIXES THAT MATTER
       * #vid gets a max-height. Without one, a portrait phone stream rendered
         ~520px tall and pushed Capture below the fold. 55vh leaves room for the
         button under it on every phone we have.
       * The capture and save bars are sticky. Even if something above them is
         tall, the thing you must press next is on screen.

     And every control a finger has to find is at least 44px tall. .btn was 33px
     and .btn.small was 22px, which is why they felt crude -- they were not ugly
     so much as hard to hit while holding a document in the other hand.
  */
  (function injectStyle(){
    if (document.getElementById("scanner-v2-style")) return;
    var st = document.createElement("style");
    st.id = "scanner-v2-style";
    st.textContent = [
      "#scanroot .btn,#scanroot button{min-height:44px;padding:11px 18px;font-size:15px;",
        "border-radius:7px;line-height:1.2}",
      "#scanroot .btn.small{min-height:44px;padding:11px 14px;font-size:14px;",
        "background:#e8edf6;color:#1f3864}",
      "#scanroot .btn.small:active{background:#d6dfef}",
      "#scanroot .btnrow{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}",
      "#scanroot .btnrow .btn{flex:1 1 auto}",
      "#scanroot .btnrow.stack .btn{flex:1 1 100%}",
      "#scanroot #vid{width:100%;max-height:55vh;object-fit:contain;display:block;",
        "border:1px solid #999;background:#000;border-radius:6px}",
      "#scanroot #cambar,#scanroot #savebar{position:sticky;bottom:0;z-index:5;",
        "background:#fff;padding:10px 0 8px;border-top:1px solid #d5deee}",
      "#scanroot #modebar{display:flex;flex-direction:column;gap:6px;margin-bottom:10px}",
      "#scanroot #modebar label{display:flex;align-items:center;gap:8px;min-height:40px;margin:0}",
      "#scanroot #modebar input{width:20px;height:20px;flex:0 0 auto}",
      "#scanroot #cv,#scanroot #ov{max-width:100%;height:auto}",
      "#scanroot input[type=text]{min-height:44px;font-size:16px;padding:8px 10px;width:100%;",
        "max-width:320px;box-sizing:border-box}",
      "#scanroot .hintline{margin:6px 0 10px}",
      "@media (prefers-color-scheme:dark){#scanroot #cambar,#scanroot #savebar{background:#161f1d}}"
    ].join("");
    document.head.appendChild(st);
  })();
  /* ===================== end v2: STYLES =================================== */

  // ---------------------------------------------------------------- UI markup
  root.innerHTML =
    '<div class=card>' +
      '<h2 style="margin-top:0">' + esc(CFG.title || "Scan document") + '</h2>' +

      '<div id=modebar style="margin-bottom:8px">' +
        '<label style="margin-right:14px"><input type=radio name=scanmode value=doc checked style="width:auto"> Document <span class=muted>(pages \u2192 one PDF)</span></label>' +
        (allowId ? '<label style="margin-right:14px"><input type=radio name=scanmode value=idcard style="width:auto"> ID card <span class=muted>(front + back on one page)</span></label>' : '') +
        (allowBatch ? '<label><input type=radio name=scanmode value=batch style="width:auto"> Batch <span class=muted>(each scan = own file)</span></label>' : '') +
      '</div>' +

      '<p id=hint class="muted hintline"></p>' +

      '<div class="btnrow" id=opencamrow>' +
        '<button type=button class=btn id=opencam style="flex:2 1 60%">\uD83D\uDCF7 Open camera</button>' +
        '<label class="btn small" style="margin:0;display:flex;align-items:center;justify-content:center">Choose photo' +
        '<input type=file id=cam accept="image/*" multiple style="display:none"></label>' +
      '</div>' +

      '<div id=camwrap style="display:none">' +
        '<video id=vid playsinline autoplay muted></video>' +
        '<div id=cambar class="btnrow">' +
          '<button type=button class=btn id=shootbtn style="flex:2 1 60%">\u25CF Capture</button>' +
          '<button type=button class="btn small" id=cancelcam>Cancel</button>' +
          '<select id=camsel style="max-width:220px;display:none"></select>' +
        '</div>' +
      '</div>' +

      '<div id=stage style="display:none">' +
        '<div style="position:relative;display:inline-block;touch-action:none">' +
          '<canvas id=cv style="max-width:100%;border:1px solid #999"></canvas>' +
          '<canvas id=ov style="position:absolute;left:0;top:0;max-width:100%"></canvas>' +
          '<canvas id=loupe width=150 height=150 style="position:absolute;top:8px;right:8px;border:3px solid #1f9dff;border-radius:75px;background:#fff;display:none;pointer-events:none"></canvas>' +
        '</div>' +
        '<p class=muted>Drag a <b>round corner</b> or a <b>square edge</b> handle (or the line) to move a whole side. A magnifier appears while you drag.</p>' +
        '<label><input type=checkbox id=bw checked style="width:auto"> Document mode (B&amp;W, flatten shadows + boost contrast)</label>' +
        '<div class="btnrow stack">' +
          '<button type=button class=btn id=addpage>\u2714 Add this page</button>' +
        '</div>' +
        '<div class="btnrow">' +
          '<button type=button class="btn small" id=addwhole>Whole image</button>' +
          '<button type=button class="btn small" id=resetcorners>Reset outline</button>' +
          '<button type=button class="btn small" id=retake>Retake</button>' +
        '</div>' +
      '</div>' +

      '<div id=pages style="margin:6px 0"></div>' +

      '<div id=savebar style="display:none;border-top:1px solid #d5deee;padding-top:8px;margin-top:6px">' +
        '<label style="display:block">File name' +
          '<span style="display:inline-flex;align-items:center;max-width:100%">' +
          '<input type=text id=fname style="max-width:280px" autocomplete=off>' +
          '<span id=fext class=muted style="margin-left:4px">.pdf</span></span>' +
        '</label>' +
        '<p><button type=button class=btn id=savebtn disabled>\uD83D\uDCBE Save</button> ' +
           '<span id=msg class=muted></span></p>' +
      '</div>' +

      '<div id=batchlist style="display:none;margin-top:8px"></div>' +
      '<p><a id=backlink href="' + esc(CFG.backUrl) + '">\u2190 back</a></p>' +
    '</div>';

  // ---------------------------------------------------------------- elements
  function $(id){ return document.getElementById(id); }
  var cv = $("cv"), ov = $("ov");
  var ctx = cv.getContext("2d"), octx = ov.getContext("2d");

  // ---------------------------------------------------------------- state
  var srcImg = null, corners = [], drag = null, last = null, stream = null;
  var pages = [];           // captured page dataURLs for the CURRENT file
  var mode = "doc";         // 'doc' | 'idcard' | 'batch'
  var idStep = 0;           // 0 = expecting front, 1 = expecting back (id mode)
  var batchSeq = 1;         // running file number in batch mode
  var savedCount = 0;
  var SCANNER_V2 = "S207.1";     // so a live page can be identified at a glance

  // ---------------------------------------------------------------- helpers
  function esc(s){ return String(s).replace(/[&<>"']/g, function(c){
    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]; }); }
  function say(t){ $("msg").textContent = t || ""; }
  function today(){ var d = new Date();
    return d.getFullYear() + "-" + String(d.getMonth()+1).padStart(2,"0") + "-" + String(d.getDate()).padStart(2,"0"); }
  function defaultName(){
    if (mode === "idcard") return CFG.nameBase + "_ICard";
    if (mode === "batch")  return CFG.nameBase + "_" + today() + "_" + batchSeq;
    return CFG.nameBase + "_" + today();
  }
  function refreshHint(){
    var h = $("hint");
    if (mode === "idcard") h.textContent = idStep === 0
      ? "ID card: capture / choose the FRONT first, add it, then the BACK."
      : "Now capture / choose the BACK. Both sides go on one page.";
    else if (mode === "batch") h.textContent = "Batch: each saved file is separate (auto-named, you can rename). File #" + batchSeq + ".";
    else h.textContent = "Add one or more pages, then Save as a single PDF.";
  }

  // ---------------------------------------------------------------- mode radios
  Array.prototype.forEach.call(document.getElementsByName("scanmode"), function(r){
    r.addEventListener("change", function(){
      mode = this.value; idStep = 0;
      pages = []; renderPages(); resetShot(); say("");
      $("batchlist").style.display = (mode === "batch" && savedCount) ? "block" : "none";
      refreshHint(); updateSaveBar();
    });
  });

  /* ======================= v2: AUTO-DETECT THE DOCUMENT ====================
     Dependency-free. No OpenCV, nothing downloaded -- this runs on the phone
     the staff already hold, on a page served from our own VPS.

     HOW IT WORKS, AND WHY THIS METHOD
       A document on a desk has one property nothing else in the frame has: a
       long, straight, high-contrast border with quiet space outside it. So:
       downscale to 320px, take the gradient magnitude, keep only the strongest
       edges, then project that energy onto the rows and the columns. The
       OUTERMOST strong column is the document's left or right edge; the
       outermost strong row is its top or bottom.

       Projecting is what makes interior text harmless. Printing inside the card
       generates plenty of gradient, but it is all INSIDE the border, so it never
       moves an outer boundary. That is the whole trick, and it is why this
       works on a driving licence, which is mostly text.

     WHAT IT DOES NOT DO
       It finds an upright rectangle, not a perspective quadrilateral. Hold the
       phone at a steep angle and the box will be honest but loose, and you drag
       the corners as before. Fixing that properly means OpenCV.js and an 8MB
       download on a phone in a pharmacy -- worth doing on evidence that this is
       not enough, not before.

     IT REFUSES RATHER THAN GUESSES
       A box smaller than 4% or larger than 96% of the frame is not a document,
       it is a failure to find one. In that case it returns null and the old
       8% inset is used, exactly as before. A wrong outline placed confidently
       is worse than the neutral one, because nobody checks a confident answer.
  */
  function autoDetect(source){
    try {
      var W = source.width, H = source.height;
      if (!W || !H) return null;
      var TW = Math.min(320, W), sc = TW / W, TH = Math.max(8, Math.round(H * sc));
      if (TH < 8 || TW < 8) return null;
      var t = document.createElement("canvas");
      t.width = TW; t.height = TH;
      t.getContext("2d").drawImage(source, 0, 0, TW, TH);
      var D = t.getContext("2d").getImageData(0, 0, TW, TH).data;
      var x, y, p, i, k;

      // ---- 1. the surface, fitted as a SHAPE and not a colour -------------
      // A desk is never one colour in a phone photo. There is a shadow across
      // it, and a flash falls off toward the corners. Fitting a flat colour and
      // calling everything else "document" is how a shadow becomes the document.
      //
      // So the surface is fitted from the ring around the frame as
      //     value = a*x + b*y + c + e*r2        (r2 = squared distance from centre)
      // per channel. The linear terms carry a shadow across the desk; the r2
      // term carries the flash falling off at the corners, which no plane can
      // hold -- that one case was 65% wrong with a flat colour and 45% wrong
      // with a plane.
      //
      // Then it is fitted a SECOND time with the worst tenth of the ring thrown
      // away. When a card or a hand touches the frame edge, the ring is partly
      // document, and an honest first fit is dragged toward it -- which cut a
      // card lying against the edge down to two-thirds of its height.
      var band = Math.max(2, Math.round(Math.min(TW, TH) * 0.05));
      var mx0 = TW / 2, my0 = TH / 2, rn = Math.max(1, mx0 * mx0 + my0 * my0);
      // The r2 term is only in the model when it EARNS its place. Fitted from a
      // ring and extrapolated into the middle of the picture, a curved surface
      // is barely constrained where it matters most -- and left switched on
      // always it bent the fitted desk up toward white in the centre and cut a
      // card on a busy desk down to two-thirds of its height. So the flat model
      // is fitted first and the curved one only replaces it when it explains
      // the ring markedly better, which is exactly the case a flash falloff
      // produces and an ordinary photo does not.
      var USE_R2 = false;
      function basis(x, y){
        var dx = (x - mx0), dy = (y - my0);
        return USE_R2 ? [1, x / TW, y / TH, (dx * dx + dy * dy) / rn]
                      : [1, x / TW, y / TH, 0];
      }
      var ring = [];
      for (y = 0; y < TH; y++) {
        for (x = 0; x < TW; x++) {
          if (x >= band && x < TW - band && y >= band && y < TH - band) continue;
          p = (y * TW + x) * 4;
          ring.push([x, y, D[p], D[p + 1], D[p + 2]]);
        }
      }
      if (ring.length < 24) return null;

      function solve4(M, v){                       // Gaussian elimination, 4x4
        var a = [], r, c2, i2, j2, piv, f;
        for (r = 0; r < 4; r++) a.push(M[r].slice().concat([v[r]]));
        for (c2 = 0; c2 < 4; c2++) {
          piv = c2;
          for (r = c2 + 1; r < 4; r++) if (Math.abs(a[r][c2]) > Math.abs(a[piv][c2])) piv = r;
          if (Math.abs(a[piv][c2]) < 1e-9) { a[c2][c2] = 1; a[c2][4] = 0; continue; }
          var tmp = a[c2]; a[c2] = a[piv]; a[piv] = tmp;
          for (r = 0; r < 4; r++) {
            if (r === c2) continue;
            f = a[r][c2] / a[c2][c2];
            for (j2 = c2; j2 <= 4; j2++) a[r][j2] -= f * a[c2][j2];
          }
        }
        var out = [];
        for (i2 = 0; i2 < 4; i2++) out.push(a[i2][4] / a[i2][i2]);
        return out;
      }
      function fit(samples){
        var co = [], ch2, r2, j3, k3, bb;
        for (ch2 = 0; ch2 < 3; ch2++) {
          var M = [[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]], v = [0,0,0,0];
          for (r2 = 0; r2 < samples.length; r2++) {
            bb = basis(samples[r2][0], samples[r2][1]);
            for (j3 = 0; j3 < 4; j3++) {
              v[j3] += bb[j3] * samples[r2][2 + ch2];
              for (k3 = 0; k3 < 4; k3++) M[j3][k3] += bb[j3] * bb[k3];
            }
          }
          var sol = solve4(M, v);
          if (!sol) return null;
          co.push(sol);
        }
        return co;
      }
      function at(co, ch2, x, y){
        var bb = basis(x, y);
        return co[ch2][0] * bb[0] + co[ch2][1] * bb[1] + co[ch2][2] * bb[2] + co[ch2][3] * bb[3];
      }
      function residual(co, smp){
        return Math.abs(smp[2] - at(co, 0, smp[0], smp[1])) +
               Math.abs(smp[3] - at(co, 1, smp[0], smp[1])) +
               Math.abs(smp[4] - at(co, 2, smp[0], smp[1]));
      }
      function med(a){ a.sort(function(u, v){ return u - v; }); return a[a.length >> 1] || 0; }

      function medResid(co2, smp){
        return med(smp.map(function(z){ return residual(co2, z); }));
      }
      USE_R2 = false;
      var coFlat = fit(ring);
      if (!coFlat) return null;
      var mFlat = medResid(coFlat, ring);
      USE_R2 = true;
      var coCurve = fit(ring);
      var mCurve = coCurve ? medResid(coCurve, ring) : Infinity;
      var co;
      if (coCurve && mCurve < mFlat * 0.75) { USE_R2 = true; co = coCurve; }
      else { USE_R2 = false; co = coFlat; }
      var rs = ring.map(function(smp){ return residual(co, smp); });
      var cut = rs.slice().sort(function(u, v){ return u - v; })[Math.floor(rs.length * 0.90)];
      var keep = ring.filter(function(smp, ix){ return rs[ix] <= cut; });
      if (keep.length >= 24) { var co2 = fit(keep); if (co2) co = co2; }

      var spread = med(keep.map(function(smp){ return residual(co, smp); }));
      if (spread > 60) return null;               // the light beats the model
      var tol = Math.max(30, spread * 3.5);
      function bgAt(ch, x, y){ return at(co, ch, x, y); }

      // ---- 2. which pixels are not the surface ----------------------------
      var colN = new Int32Array(TW), rowN = new Int32Array(TH), d;
      for (y = 0; y < TH; y++) {
        for (x = 0; x < TW; x++) {
          p = (y * TW + x) * 4;
          d = Math.abs(D[p] - bgAt(0, x, y)) + Math.abs(D[p + 1] - bgAt(1, x, y)) +
              Math.abs(D[p + 2] - bgAt(2, x, y));
          if (d > tol) { colN[x]++; rowN[y]++; }
        }
      }

      // ---- 3. the WIDEST run, not the outermost ---------------------------
      // A finger resting at the edge of the frame is also "not the surface".
      // Taking the outermost qualifying column stretched the box to the frame
      // edge and swallowed it. The document is the biggest coherent thing in
      // the picture, so the widest unbroken run wins and the finger is left out.
      function widestRun(prof, len, other){
        var need = Math.max(3, Math.round(other * 0.12));
        // A short gap does not end the document. Shrinking the picture to 320px
        // blends a dark text line into the white around it, and where that
        // average happens to land on the colour of the desk, one single row
        // reads as background -- a one-pixel slit straight across the card.
        // That split the run in two and handed back the top two-thirds of a
        // licence, confidently. Nothing real has a slit like that, so gaps
        // under 2% of the side are bridged.
        var maxGap = Math.max(1, Math.round(len * 0.02));
        var best = null, s0 = -1, gap = 0, lastOn = -1;
        for (k = 0; k <= len; k++) {
          var on = (k < len) && (prof[k] >= need);
          if (on) {
            if (s0 < 0) s0 = k;
            lastOn = k; gap = 0;
          } else if (s0 >= 0) {
            gap++;
            if (gap > maxGap || k === len) {
              if (!best || (lastOn - s0) > (best[1] - best[0])) best = [s0, lastOn];
              s0 = -1; gap = 0;
            }
          }
        }
        return (best && best[1] > best[0]) ? best : null;
      }
      var cx = widestRun(colN, TW, TH), cy = widestRun(rowN, TH, TW);
      if (window.__scannerDebug) {
        window.__scannerDebug = {TW: TW, TH: TH, tol: tol, spread: spread,
                                 curved: USE_R2, colN: Array.from(colN),
                                 rowN: Array.from(rowN), cx: cx, cy: cy};
      }
      if (!cx || !cy) return null;

      var frac = ((cx[1] - cx[0] + 1) * (cy[1] - cy[0] + 1)) / (TW * TH);
      if (frac < 0.04 || frac > 0.985) return null;

      // ---- 4. does the box actually SIT on an edge? -----------------------
      // The last failure this catches is the quiet one. If the document fills
      // the whole frame, the ring samples the DOCUMENT, the paper becomes the
      // "surface", and the only thing left standing out is the printing -- so
      // the box lands neatly around the text block and looks entirely
      // plausible. Checking that the pixels just outside the box differ from
      // those just inside is what tells the two apart: a real border has a
      // step across it, a text block does not.
      function meanAt(px, py, r){
        var sm = 0, c2 = 0, ax, ay;
        for (ay = Math.max(0, py - r); ay <= Math.min(TH - 1, py + r); ay++) {
          for (ax = Math.max(0, px - r); ax <= Math.min(TW - 1, px + r); ax++) {
            p = (ay * TW + ax) * 4; sm += 0.3 * D[p] + 0.59 * D[p + 1] + 0.11 * D[p + 2]; c2++;
          }
        }
        return c2 ? sm / c2 : 0;
      }
      var steps = [], mid, gap = Math.max(3, Math.round(Math.min(TW, TH) * 0.03));
      mid = (cy[0] + cy[1]) >> 1;
      if (cx[0] - gap >= 0) steps.push(Math.abs(meanAt(cx[0] + gap, mid, 2) - meanAt(cx[0] - gap, mid, 2)));
      if (cx[1] + gap < TW) steps.push(Math.abs(meanAt(cx[1] - gap, mid, 2) - meanAt(cx[1] + gap, mid, 2)));
      mid = (cx[0] + cx[1]) >> 1;
      if (cy[0] - gap >= 0) steps.push(Math.abs(meanAt(mid, cy[0] + gap, 2) - meanAt(mid, cy[0] - gap, 2)));
      if (cy[1] + gap < TH) steps.push(Math.abs(meanAt(mid, cy[1] - gap, 2) - meanAt(mid, cy[1] + gap, 2)));
      if (!steps.length) return null;
      var strong = 0;
      for (i = 0; i < steps.length; i++) if (steps[i] > 10) strong++;
      if (strong < Math.min(2, steps.length)) return null;

      var k2 = 1 / sc;
      var L = Math.max(0, cx[0] * k2), R = Math.min(W, (cx[1] + 1) * k2);
      var T = Math.max(0, cy[0] * k2), Bm = Math.min(H, (cy[1] + 1) * k2);
      if (R - L < 8 || Bm - T < 8) return null;
      return [[L, T], [R, T], [R, Bm], [L, Bm]];
    } catch (e) { return null; }
  }
  window.__scannerAutoDetect = autoDetect;   // exposed so the selftest can drive it
  /* ===================== end v2: AUTO-DETECT ============================== */

  // ---------------------------------------------------------------- image load
  function loadImage(src){
    var img = new Image();
    img.onload = function(){
      var s = Math.min(1, 1400 / Math.max(img.width, img.height));
      cv.width = ov.width = Math.round(img.width * s);
      cv.height = ov.height = Math.round(img.height * s);
      ctx.drawImage(img, 0, 0, cv.width, cv.height); srcImg = img;
      // v2: put the outline ON the document. Falls back to the old 8% inset
      // whenever detection is not confident -- see autoDetect above.
      var found = autoDetect(cv);
      if (found) {
        corners = found;
        say("Outline placed automatically \u2014 drag a corner if it needs nudging.");
      } else {
        var mx = cv.width * 0.08, my = cv.height * 0.08;
        corners = [[mx,my],[cv.width-mx,my],[cv.width-mx,cv.height-my],[mx,cv.height-my]];
        say("Could not find the edges \u2014 drag the corners onto the document.");
      }
      $("stage").style.display = "block"; drawOverlay();
      $("stage").scrollIntoView({behavior:"smooth", block:"nearest"});
    };
    img.onerror = function(){ say("Could not read that image."); };
    img.src = src;
  }
  // multi-file import: queue them; when one is added the next auto-loads
  var importQueue = [];
  function loadNextImport(){
    if (!importQueue.length) return;
    loadImage(URL.createObjectURL(importQueue.shift()));
  }
  $("cam").addEventListener("change", function(e){
    var files = Array.prototype.slice.call(e.target.files || []);
    if (!files.length) return;
    importQueue = files; loadNextImport();
  });

  // ---------------------------------------------------------------- live camera (verbatim v1.2.0)
  function camSupported(){ return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia); }
  function openCam(){
    if (!camSupported()){ say('This browser has no camera access (needs https). Use "Choose photo(s)".'); return; }
    var want = {video:{facingMode:{ideal:"environment"}, width:{ideal:1920}, height:{ideal:1440}}, audio:false};
    navigator.mediaDevices.getUserMedia(want).then(startStream).catch(function(){
      navigator.mediaDevices.getUserMedia({video:true, audio:false}).then(startStream).catch(function(err){
        say('Camera unavailable (' + (err && err.name ? err.name : "error") + '). Use "Choose photo(s)".');
      });
    });
  }
  function startStream(st){
    stream = st;
    var v = $("vid"); v.srcObject = st; v.play();
    $("camwrap").style.display = "block";
    // v2: while you are aiming, nothing else on the page is any use -- the mode
    // radios, the hint and the open-camera row are ~160px of screen that push
    // Capture toward the fold. Measured at 390x780 the button cleared the
    // bottom by 8px with them showing, which is no margin at all once a browser
    // puts its own bars on the screen. They come straight back on cancel.
    camChrome(false);
    say(""); listCams();
  }
  function camChrome(show){
    var d = show ? "" : "none";
    ["modebar", "hint", "opencamrow"].forEach(function(id){
      var e = $(id); if (e) e.style.display = d;
    });
  }
  function listCams(){
    if (!navigator.mediaDevices.enumerateDevices) return;
    navigator.mediaDevices.enumerateDevices().then(function(ds){
      var cams = ds.filter(function(d){ return d.kind === "videoinput"; });
      if (cams.length < 2) return;
      var sel = $("camsel"); sel.innerHTML = "";
      cams.forEach(function(c,i){ var o = document.createElement("option");
        o.value = c.deviceId; o.textContent = c.label || ("Camera " + (i+1)); sel.appendChild(o); });
      sel.style.display = "inline-block";
      sel.onchange = function(){
        stopStream();
        navigator.mediaDevices.getUserMedia({video:{deviceId:{exact:sel.value}}, audio:false})
          .then(function(st){ stream = st; $("vid").srcObject = st; });
      };
    }).catch(function(){});
  }
  function shoot(){
    var v = $("vid");
    if (!v.videoWidth){ say("Camera still starting — try again in a second."); return; }
    var c = document.createElement("canvas");
    c.width = v.videoWidth; c.height = v.videoHeight;
    c.getContext("2d").drawImage(v, 0, 0, c.width, c.height);
    loadImage(c.toDataURL("image/jpeg", 0.92)); closeCam();
  }
  function stopStream(){ if (stream){ stream.getTracks().forEach(function(t){ t.stop(); }); stream = null; } }
  function closeCam(){
    stopStream();
    $("camwrap").style.display = "none";
    camChrome(true);
    $("opencam").textContent = "\uD83D\uDCF7 Open camera";
  }
  window.addEventListener("pagehide", stopStream);
  window.addEventListener("beforeunload", stopStream);
  if (!camSupported()) $("opencam").style.display = "none";

  // ---------------------------------------------------------------- crop overlay (verbatim v1.2.0)
  function kScale(){ var r = ov.getBoundingClientRect(); return r.width ? ov.width / r.width : 1; }
  function mid(i){ var a = corners[i], b = corners[(i+1)%4]; return [(a[0]+b[0])/2, (a[1]+b[1])/2]; }
  function clampPt(p){ return [Math.max(0,Math.min(ov.width,p[0])), Math.max(0,Math.min(ov.height,p[1]))]; }
  function drawOverlay(){
    var k = kScale();
    octx.clearRect(0,0,ov.width,ov.height);
    octx.save();
    octx.beginPath(); octx.rect(0,0,ov.width,ov.height);
    octx.moveTo(corners[0][0],corners[0][1]);
    for (var i=3;i>=0;i--){ octx.lineTo(corners[i][0],corners[i][1]); }
    octx.closePath(); octx.fillStyle = "rgba(0,0,0,.35)"; octx.fill("evenodd"); octx.restore();
    octx.strokeStyle = "#1f9dff"; octx.lineWidth = Math.max(2,3*k); octx.beginPath();
    octx.moveTo(corners[0][0],corners[0][1]);
    for (var j=1;j<5;j++){ var p = corners[j%4]; octx.lineTo(p[0],p[1]); }
    octx.stroke();
    for (var e=0;e<4;e++){ var m = mid(e), h = 11*k;
      octx.fillStyle = (drag && drag.type==="e" && drag.i===e) ? "#ff9500" : "rgba(31,157,255,.9)";
      octx.fillRect(m[0]-h,m[1]-h,h*2,h*2);
      octx.strokeStyle = "#fff"; octx.lineWidth = Math.max(1,2*k); octx.strokeRect(m[0]-h,m[1]-h,h*2,h*2); }
    corners.forEach(function(p,i){
      octx.fillStyle = (drag && drag.type==="c" && drag.i===i) ? "#ff9500" : "rgba(31,157,255,.9)";
      octx.beginPath(); octx.arc(p[0],p[1],15*k,0,7); octx.fill();
      octx.strokeStyle = "#fff"; octx.lineWidth = Math.max(1,2*k); octx.stroke(); });
  }
  function evPos(e){ var r = ov.getBoundingClientRect(), t = (e.touches && e.touches[0]) ? e.touches[0] : e;
    return [(t.clientX-r.left)*ov.width/r.width, (t.clientY-r.top)*ov.height/r.height]; }
  function d2(a,b){ return (a[0]-b[0])*(a[0]-b[0]) + (a[1]-b[1])*(a[1]-b[1]); }
  function segD2(p,a,b){ var vx=b[0]-a[0], vy=b[1]-a[1], L=vx*vx+vy*vy;
    if (!L) return d2(p,a);
    var t = Math.max(0,Math.min(1,((p[0]-a[0])*vx + (p[1]-a[1])*vy)/L));
    return d2(p,[a[0]+t*vx, a[1]+t*vy]); }
  function hitTest(p){ var k=kScale(), rc=Math.pow(26*k,2), re=Math.pow(22*k,2), rl=Math.pow(16*k,2), i;
    for (i=0;i<4;i++){ if (d2(p,corners[i])<rc) return {type:"c",i:i}; }
    for (i=0;i<4;i++){ if (d2(p,mid(i))<re) return {type:"e",i:i}; }
    for (i=0;i<4;i++){ if (segD2(p,corners[i],corners[(i+1)%4])<rl) return {type:"e",i:i}; }
    return null; }
  function moveEdge(i,dx,dy){ var a=corners[i], b=corners[(i+1)%4];
    var ex=b[0]-a[0], ey=b[1]-a[1], L=Math.hypot(ex,ey)||1, nx=-ey/L, ny=ex/L, d=dx*nx+dy*ny;
    corners[i]=clampPt([a[0]+nx*d,a[1]+ny*d]); corners[(i+1)%4]=clampPt([b[0]+nx*d,b[1]+ny*d]); }
  function showLoupe(p){ var L=$("loupe"), lc=L.getContext("2d"), z=3.2, s=L.width/z;
    lc.clearRect(0,0,L.width,L.height);
    lc.drawImage(cv, p[0]-s/2, p[1]-s/2, s, s, 0, 0, L.width, L.height);
    lc.strokeStyle="#1f9dff"; lc.lineWidth=1.5; lc.beginPath();
    lc.moveTo(L.width/2-12,L.height/2); lc.lineTo(L.width/2+12,L.height/2);
    lc.moveTo(L.width/2,L.height/2-12); lc.lineTo(L.width/2,L.height/2+12); lc.stroke();
    var rightHalf = p[0] > ov.width/2;
    L.style.right = rightHalf ? "auto" : "8px"; L.style.left = rightHalf ? "8px" : "auto";
    L.style.display = "block"; }
  function hideLoupe(){ $("loupe").style.display = "none"; }
  function resetCorners(){ var mx=ov.width*0.08, my=ov.height*0.08;
    corners=[[mx,my],[ov.width-mx,my],[ov.width-mx,ov.height-my],[mx,ov.height-my]]; drawOverlay(); }
  function down(e){ var p=evPos(e); drag=hitTest(p);
    if (drag){ last=p; e.preventDefault(); drawOverlay(); showLoupe(p); } }
  function move(e){ if (!drag) return; e.preventDefault(); var p=evPos(e);
    if (drag.type==="c"){ corners[drag.i]=clampPt(p); } else { moveEdge(drag.i, p[0]-last[0], p[1]-last[1]); }
    last=p; drawOverlay(); showLoupe(p); }
  function up(){ if (drag){ drag=null; hideLoupe(); drawOverlay(); } }
  ov.addEventListener("mousedown",down); ov.addEventListener("mousemove",move); addEventListener("mouseup",up);
  ov.addEventListener("touchstart",down,{passive:false}); ov.addEventListener("touchmove",move,{passive:false});
  ov.addEventListener("touchend",up); ov.addEventListener("touchcancel",up);

  // ---------------------------------------------------------------- image enhance (A-D18)
  // Flatten uneven lighting/shadows (common in phone bill photos) via integral-image
  // local-mean normalization, then a global contrast stretch. Preserves grays (stamps,
  // handwriting) far better than a global-only stretch -> cleaner OCR input.
  function enhanceGray(D, W, H){
    var Wp=W+1, integ=new Float64Array(Wp*(H+1)), x, y, i, p, gy;
    for (y=0;y<H;y++){ var rowsum=0;
      for (x=0;x<W;x++){ p=(y*W+x)*4; gy=0.3*D[p]+0.59*D[p+1]+0.11*D[p+2];
        rowsum+=gy; integ[(y+1)*Wp+(x+1)]=integ[y*Wp+(x+1)]+rowsum; } }
    var s=Math.max(15, Math.floor((W<H?W:H)/8)), half=s>>1;
    var minv=1e9, maxv=-1e9, out=new Float32Array(W*H);
    for (y=0;y<H;y++){ var y1=y-half<0?0:y-half, y2=y+half>=H?H-1:y+half;
      for (x=0;x<W;x++){ var x1=x-half<0?0:x-half, x2=x+half>=W?W-1:x+half;
        var cnt=(x2-x1+1)*(y2-y1+1);
        var sum=integ[(y2+1)*Wp+(x2+1)]-integ[y1*Wp+(x2+1)]-integ[(y2+1)*Wp+x1]+integ[y1*Wp+x1];
        var mean=sum/cnt; p=(y*W+x)*4; gy=0.3*D[p]+0.59*D[p+1]+0.11*D[p+2];
        var norm=mean>0?(gy/mean)*200:gy; if(norm>255)norm=255;
        out[y*W+x]=norm; if(norm<minv)minv=norm; if(norm>maxv)maxv=norm; } }
    var rng=maxv-minv; if(rng<1)rng=1;
    for (i=0;i<W*H;i++){ var g2=Math.round((out[i]-minv)*255/rng); if(g2<0)g2=0; if(g2>255)g2=255;
      p=i*4; D[p]=D[p+1]=D[p+2]=g2; } }

  // ---------------------------------------------------------------- warp (verbatim v1.2.0)
  function warp(){
    // Heckbert unit-square -> quad homography, inverse-sampled
    var c=corners, x0=c[0][0],y0=c[0][1],x1=c[1][0],y1=c[1][1],x2=c[2][0],y2=c[2][1],x3=c[3][0],y3=c[3][1];
    var W=Math.round((Math.hypot(x1-x0,y1-y0)+Math.hypot(x2-x3,y2-y3))/2);
    var H=Math.round((Math.hypot(x3-x0,y3-y0)+Math.hypot(x2-x1,y2-y1))/2);
    var s=Math.min(1,1600/Math.max(W,H)); W=Math.max(50,Math.round(W*s)); H=Math.max(50,Math.round(H*s));
    var dx1=x1-x2,dx2=x3-x2,dx3=x0-x1+x2-x3,dy1=y1-y2,dy2=y3-y2,dy3=y0-y1+y2-y3,a,b,cc,d,e,f,g,h;
    if (Math.abs(dx3)<1e-9 && Math.abs(dy3)<1e-9){ a=x1-x0;b=x3-x0;cc=x0;d=y1-y0;e=y3-y0;f=y0;g=0;h=0; }
    else { var den=dx1*dy2-dx2*dy1; g=(dx3*dy2-dx2*dy3)/den; h=(dx1*dy3-dx3*dy1)/den;
      a=x1-x0+g*x1; b=x3-x0+h*x3; cc=x0; d=y1-y0+g*y1; e=y3-y0+h*y3; f=y0; }
    var sd=ctx.getImageData(0,0,cv.width,cv.height).data, sw=cv.width, sh=cv.height;
    var out=document.createElement("canvas"); out.width=W; out.height=H;
    var oc=out.getContext("2d"), od=oc.createImageData(W,H), D=od.data, k=0;
    for (var r=0;r<H;r++){ var v=r/H;
      for (var q=0;q<W;q++){ var u=q/W, w=g*u+h*v+1;
        var X=Math.round((a*u+b*v+cc)/w), Y=Math.round((d*u+e*v+f)/w);
        if (X>=0 && Y>=0 && X<sw && Y<sh){ var si=(Y*sw+X)*4; D[k]=sd[si]; D[k+1]=sd[si+1]; D[k+2]=sd[si+2]; }
        else { D[k]=D[k+1]=D[k+2]=255; }
        D[k+3]=255; k+=4; } }
    if ($("bw").checked){ enhanceGray(D, W, H); }
    oc.putImageData(od,0,0); return out;
  }
  // whole-image, no perspective correction (for already-clean photos)
  function wholeImage(){
    var out=document.createElement("canvas"); out.width=cv.width; out.height=cv.height;
    out.getContext("2d").drawImage(cv,0,0);
    if ($("bw").checked){
      var oc=out.getContext("2d"), od=oc.getImageData(0,0,out.width,out.height);
      enhanceGray(od.data, out.width, out.height);
      oc.putImageData(od,0,0);
    }
    return out;
  }

  // ---------------------------------------------------------------- pages
  function addCaptured(canvas){
    pages.push(canvas.toDataURL("image/jpeg", 0.85));
    renderPages(); resetShot();
    if (mode === "idcard"){
      idStep = pages.length >= 1 ? 1 : 0;
      if (pages.length >= 2){ idStep = 1; }
      refreshHint();
    }
    updateSaveBar();
  }
  function addPage(){ addCaptured(warp()); }
  function addWhole(){ addCaptured(wholeImage()); }

  function renderPages(){
    var box = $("pages"); box.innerHTML = "";
    pages.forEach(function(du, i){
      var wrap = document.createElement("span");
      wrap.style.cssText = "position:relative;display:inline-block;margin:3px";
      var t = document.createElement("img"); t.src = du;
      t.style.cssText = "height:90px;border:1px solid #999;display:block";
      var lbl = document.createElement("span");
      lbl.textContent = (mode === "idcard" ? (i===0?"Front":i===1?"Back":("Pg "+(i+1))) : ("Pg "+(i+1)));
      lbl.style.cssText = "position:absolute;left:2px;bottom:2px;background:rgba(0,0,0,.6);color:#fff;font-size:11px;padding:0 4px;border-radius:3px";
      var x = document.createElement("button"); x.type="button"; x.textContent="\u2715";
      x.title = "Delete this page";
      x.style.cssText = "position:absolute;top:-8px;right:-8px;width:22px;height:22px;border-radius:11px;border:none;background:#c0392b;color:#fff;cursor:pointer;line-height:1";
      x.onclick = function(){ pages.splice(i,1);
        if (mode==="idcard"){ idStep = pages.length>=2?1:pages.length; }
        renderPages(); refreshHint(); updateSaveBar(); };
      wrap.appendChild(t); wrap.appendChild(lbl); wrap.appendChild(x); box.appendChild(wrap);
    });
  }

  function resetShot(){ $("stage").style.display = "none"; $("cam").value = "";
    // continue a multi-file import if more were queued
    if (importQueue.length) setTimeout(loadNextImport, 150); }

  // ---------------------------------------------------------------- save bar
  function updateSaveBar(){
    var ready = pages.length > 0 && (mode !== "idcard" || pages.length >= 2);
    $("savebar").style.display = pages.length ? "block" : "none";
    $("savebtn").disabled = !ready;
    $("fname").value = defaultName();
    $("savebtn").textContent = (mode === "batch") ? "\uD83D\uDCBE Save this file" : "\uD83D\uDCBE Save";
  }

  // ---------------------------------------------------------------- compose ID card (2-up, one A4 page)
  function composeIdCard(cb){
    var page = document.createElement("canvas"); page.width = 1240; page.height = 1754; // ~A4 @150dpi
    var pc = page.getContext("2d"); pc.fillStyle = "#fff"; pc.fillRect(0,0,page.width,page.height);
    var slots = [[0.06,0.06,0.88,0.42],[0.06,0.52,0.88,0.42]]; // x,y,w,h as fractions (top / bottom)
    var loaded = 0, imgs = [];
    var take = Math.min(2, pages.length);
    for (var i=0;i<take;i++){
      (function(idx){
        var im = new Image();
        im.onload = function(){ imgs[idx] = im; if (++loaded === take) paint(); };
        im.onerror = function(){ if (++loaded === take) paint(); };
        im.src = pages[idx];
      })(i);
    }
    function paint(){
      for (var i=0;i<take;i++){
        var im = imgs[i]; if (!im) continue;
        var s = slots[i], bx = s[0]*page.width, by = s[1]*page.height, bw = s[2]*page.width, bh = s[3]*page.height;
        var r = Math.min(bw/im.width, bh/im.height), w = im.width*r, h = im.height*r;
        pc.drawImage(im, bx+(bw-w)/2, by+(bh-h)/2, w, h);
      }
      cb(page.toDataURL("image/jpeg", 0.9));
    }
  }

  // ---------------------------------------------------------------- PDF assembly
  function pagesToBlob(pageList, cb){
    if (window.jspdf){
      var pdf = new window.jspdf.jsPDF({unit:"mm", format:"a4"});
      pageList.forEach(function(du, i){
        if (i>0) pdf.addPage();
        var im = new Image(); im.src = du;
        var pw = 210-16, ph = 297-16, ratio = (im.height/im.width) || 1.4;
        var w = pw, h = pw*ratio; if (h>ph){ h=ph; w=ph/ratio; }
        pdf.addImage(du, "JPEG", 8, 8, w, h);
      });
      cb(pdf.output("blob"), "pdf", "");
    } else {
      // CDN unreachable: fall back to first page as JPEG
      var bin = atob(pageList[0].split(",")[1]), arr = new Uint8Array(bin.length);
      for (var i=0;i<bin.length;i++) arr[i] = bin.charCodeAt(i);
      cb(new Blob([arr], {type:"image/jpeg"}), "jpg", "PDF library unreachable — saved page 1 as JPEG. ");
    }
  }

  // ---------------------------------------------------------------- upload
  function upload(blob, filename){
    var fd = new FormData();
    Object.keys(CFG.uploadFields).forEach(function(k){ fd.append(k, CFG.uploadFields[k]); });
    fd.append(CFG.fileField, blob, filename);
    say("Uploading\u2026");
    return fetch(CFG.uploadUrl, {method:"POST", body:fd}).then(function(r){
      if (!r.ok) throw new Error("HTTP " + r.status);
      return true;
    });
  }
  function cleanName(v, ext){
    v = (v || defaultName()).trim().replace(/[\\/:*?"<>|]+/g, "_").replace(/\s+/g, "_");
    if (!v) v = defaultName();
    if (v.toLowerCase().slice(-(ext.length+1)) !== ("." + ext)) v = v + "." + ext;
    return v;
  }

  // ---------------------------------------------------------------- save actions
  function doSave(){
    if (!pages.length) return;
    $("savebtn").disabled = true;
    var assemble = function(list){
      pagesToBlob(list, function(blob, ext, note){
        var fname = cleanName($("fname").value, ext);
        upload(blob, fname).then(function(){
          if (mode === "batch"){
            savedCount++; batchSeq++;
            addBatchRow(fname);
            pages = []; renderPages(); updateSaveBar();
            say(note + "Saved \u2713 — ready for the next.");
          } else {
            say(note + "Saved \u2713");
            window.location = CFG.backUrl;
          }
        }).catch(function(err){ say("Upload failed (" + err.message + ")"); $("savebtn").disabled = false; });
      });
    };
    if (mode === "idcard"){ composeIdCard(function(du){ assemble([du]); }); }
    else { assemble(pages.slice()); }
  }
  function addBatchRow(fname){
    var box = $("batchlist"); box.style.display = "block";
    if (!box.dataset.init){ box.dataset.init = "1";
      box.innerHTML = "<b>Saved this session:</b>"; }
    var d = document.createElement("div"); d.className = "muted";
    d.textContent = "\u2713 " + fname; box.appendChild(d);
  }

  // ---------------------------------------------------------------- wire buttons
  $("opencam").addEventListener("click", openCam);
  $("shootbtn").addEventListener("click", shoot);
  $("cancelcam").addEventListener("click", closeCam);
  $("addpage").addEventListener("click", addPage);
  $("addwhole").addEventListener("click", addWhole);
  $("resetcorners").addEventListener("click", resetCorners);
  $("retake").addEventListener("click", resetShot);
  $("savebtn").addEventListener("click", doSave);

  refreshHint(); updateSaveBar();
})();
