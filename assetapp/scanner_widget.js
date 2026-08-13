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
 * filename before every save. Image-quality upgrades (auto-detect / bilinear /
 * adaptive B&W) are Stage 1B and deliberately NOT here.
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

  // ---------------------------------------------------------------- UI markup
  root.innerHTML =
    '<div class=card>' +
      '<h2 style="margin-top:0">' + esc(CFG.title || "Scan document") + '</h2>' +

      '<div id=modebar style="margin-bottom:8px">' +
        '<label style="margin-right:14px"><input type=radio name=scanmode value=doc checked style="width:auto"> Document <span class=muted>(pages \u2192 one PDF)</span></label>' +
        (allowId ? '<label style="margin-right:14px"><input type=radio name=scanmode value=idcard style="width:auto"> ID card <span class=muted>(front + back on one page)</span></label>' : '') +
        (allowBatch ? '<label><input type=radio name=scanmode value=batch style="width:auto"> Batch <span class=muted>(each scan = own file)</span></label>' : '') +
      '</div>' +

      '<p id=hint class=muted style="margin:4px 0"></p>' +

      '<p><button type=button class=btn id=opencam>\uD83D\uDCF7 Open camera</button>' +
      '<span class=muted style="margin:0 8px">or</span>' +
      '<label class="btn small" style="margin:0">\uD83D\uDDBC Choose photo(s)' +
      '<input type=file id=cam accept="image/*" multiple style="display:none"></label></p>' +

      '<div id=camwrap style="display:none">' +
        '<video id=vid playsinline autoplay muted style="max-width:100%;border:1px solid #999;background:#000"></video>' +
        '<p><button type=button class=btn id=shootbtn>\u25CF Capture</button>' +
        '<button type=button class="btn small" id=cancelcam>Cancel</button>' +
        '<select id=camsel style="max-width:220px;display:none"></select></p>' +
      '</div>' +

      '<div id=stage style="display:none">' +
        '<div style="position:relative;display:inline-block;touch-action:none">' +
          '<canvas id=cv style="max-width:100%;border:1px solid #999"></canvas>' +
          '<canvas id=ov style="position:absolute;left:0;top:0;max-width:100%"></canvas>' +
          '<canvas id=loupe width=150 height=150 style="position:absolute;top:8px;right:8px;border:3px solid #1f9dff;border-radius:75px;background:#fff;display:none;pointer-events:none"></canvas>' +
        '</div>' +
        '<p class=muted>Drag a <b>round corner</b> or a <b>square edge</b> handle (or the line) to move a whole side. A magnifier appears while you drag.</p>' +
        '<label><input type=checkbox id=bw checked style="width:auto"> Document mode (B&amp;W contrast boost)</label>' +
        '<p><button type=button class=btn id=addpage>\u2714 Add page</button>' +
           '<button type=button class="btn small" id=addwhole>\u2795 Add whole image (no crop)</button>' +
           '<button type=button class="btn small" id=resetcorners>\u21BA Reset outline</button>' +
           '<button type=button class="btn small" id=retake>\u21BA Retake</button></p>' +
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

  // ---------------------------------------------------------------- image load
  function loadImage(src){
    var img = new Image();
    img.onload = function(){
      var s = Math.min(1, 1400 / Math.max(img.width, img.height));
      cv.width = ov.width = Math.round(img.width * s);
      cv.height = ov.height = Math.round(img.height * s);
      ctx.drawImage(img, 0, 0, cv.width, cv.height); srcImg = img;
      var mx = cv.width * 0.08, my = cv.height * 0.08;
      corners = [[mx,my],[cv.width-mx,my],[cv.width-mx,cv.height-my],[mx,cv.height-my]];
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
    $("opencam").textContent = "\uD83D\uDCF7 Camera on";
    say(""); listCams();
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
    if ($("bw").checked){
      var hist=new Array(256).fill(0), n=W*H;
      for (var i=0;i<D.length;i+=4){ var gy=Math.round(.3*D[i]+.59*D[i+1]+.11*D[i+2]); D[i]=gy; hist[gy]++; }
      var lo=0, hi=255, acc=0;
      for (var lp=0;lp<256;lp++){ acc+=hist[lp]; if (acc>n*0.05){ lo=lp; break; } }
      acc=0; for (var hp=255;hp>=0;hp--){ acc+=hist[hp]; if (acc>n*0.05){ hi=hp; break; } }
      var rng=Math.max(1,hi-lo);
      for (var j=0;j<D.length;j+=4){ var gv=Math.max(0,Math.min(255,Math.round((D[j]-lo)*255/rng)));
        D[j]=D[j+1]=D[j+2]=gv; } }
    oc.putImageData(od,0,0); return out;
  }
  // whole-image, no perspective correction (for already-clean photos)
  function wholeImage(){
    var out=document.createElement("canvas"); out.width=cv.width; out.height=cv.height;
    out.getContext("2d").drawImage(cv,0,0);
    if ($("bw").checked){
      var oc=out.getContext("2d"), od=oc.getImageData(0,0,out.width,out.height), D=od.data, n=out.width*out.height;
      var hist=new Array(256).fill(0);
      for (var i=0;i<D.length;i+=4){ var gy=Math.round(.3*D[i]+.59*D[i+1]+.11*D[i+2]); D[i]=gy; hist[gy]++; }
      var lo=0, hi=255, acc=0;
      for (var lp=0;lp<256;lp++){ acc+=hist[lp]; if (acc>n*0.05){ lo=lp; break; } }
      acc=0; for (var hp=255;hp>=0;hp--){ acc+=hist[hp]; if (acc>n*0.05){ hi=hp; break; } }
      var rng=Math.max(1,hi-lo);
      for (var j=0;j<D.length;j+=4){ var gv=Math.max(0,Math.min(255,Math.round((D[j]-lo)*255/rng)));
        D[j]=D[j+1]=D[j+2]=gv; }
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
