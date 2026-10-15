// S563 browser walk -- the desk with F-902's line: a set-aside paper opened, measured as S560's layout.js measures (every
// destination button, the kinds, Save, the join / blank row by their bounding rectangles); then the line, its Restore
// button, and Save held ("Restore it first (above)") once a destination is chosen.
(function () {
  function $(i) { return document.getElementById(i); }
  function vis(el) {
    if (!el) { return false; }
    var r = el.getBoundingClientRect(), f = $("fields").getBoundingClientRect(), inF = $("fields").contains(el);
    var onScreen = r.width > 0 && r.height > 0 && r.top >= 0 && r.left >= 0 && r.bottom <= window.innerHeight + 0.5 && r.right <= window.innerWidth + 0.5;
    var inPanel = !inF || (r.top >= f.top - 0.5 && r.bottom <= f.bottom + 0.5);
    return onScreen && inPanel;
  }
  function label(el) { return (el.textContent || el.id || "").trim().slice(0, 40); }
  function report() {
    var out = { vw: window.innerWidth, vh: window.innerHeight, errs: window.__errs || [] };
    var dests = Array.prototype.slice.call(document.querySelectorAll("#groups .d"));
    var kinds = Array.prototype.slice.call(document.querySelectorAll("#kinds .b"));
    out.pageboxShown = $("pagebox").style.display !== "none";   // a set-aside paper is never offered the join / blank row (as today)
    var other = kinds.concat([$("save")], out.pageboxShown ? [$("pagebox"), $("blank"), $("pg_on")] : []);
    out.nDest = dests.length; out.nKind = kinds.length;
    out.below = dests.filter(function (e) { return !vis(e); }).map(function (e) { var g = e.closest(".grp"); return g ? g.querySelector(".gt").textContent : ""; });
    out.hiddenOther = other.filter(function (e) { return !vis(e); }).map(label);
    out.cue = !!$("morecue") && $("morecue").style.display !== "none" && vis($("morecue"));
    out.pageScroll = document.documentElement.scrollHeight > window.innerHeight + 1 || document.documentElement.scrollWidth > window.innerWidth + 1;
    var a = $("s563aside");
    out.asideText = a ? a.querySelector("b").textContent : "";
    out.asideCount = document.querySelectorAll("#s563aside").length;
    out.restoreCount = document.querySelectorAll("[data-restore],[data-fix=restore]").length;
    out.asideVis = vis(a); out.restoreVis = vis(document.querySelector("[data-restore]"));
    out.saveOn0 = !$("save").disabled; out.saveText0 = $("save").textContent;
    var d = document.querySelector('#groups [data-d="others"]'); if (d) { d.click(); }
    out.saveOn1 = !$("save").disabled; out.saveText1 = $("save").textContent;
    out.status = $("status").textContent;
    (window.__realFetch || window.fetch)("/result", { method: "POST", body: JSON.stringify(out) });
  }
  var t0 = Date.now();
  (function wait() {
    var h = $("hstamp");
    if (h && h.textContent && h.textContent !== "—" && document.querySelectorAll("#groups .d").length) { return setTimeout(report, 400); }
    if (Date.now() - t0 > 15000) { return (window.fetch)("/result", { method: "POST", body: JSON.stringify({ errs: ["the paper did not open in 15 s"] }) }); }
    setTimeout(wait, 100);
  })();
})();
