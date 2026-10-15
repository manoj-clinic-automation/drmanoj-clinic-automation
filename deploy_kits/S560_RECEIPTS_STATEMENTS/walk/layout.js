// S560 browser walk -- the desk on one screen: every destination button, the kind buttons, Save and the join / blank row,
// measured by their bounding rectangles once the paper is drawn; then the Receipt and Statement views (scene from ?sc=).
(function () {
  var SC = (location.search.match(/sc=(\w+)/) || [])[1] || "bill";
  function $(i) { return document.getElementById(i); }
  function vis(el) {                                    // fully on screen AND inside the right panel's visible area (no scrolling)
    var r = el.getBoundingClientRect(), f = $("fields").getBoundingClientRect(), inF = $("fields").contains(el);
    var onScreen = r.width > 0 && r.height > 0 && r.top >= 0 && r.left >= 0 && r.bottom <= window.innerHeight + 0.5 && r.right <= window.innerWidth + 0.5;
    var inPanel = !inF || (r.top >= f.top - 0.5 && r.bottom <= f.bottom + 0.5);
    return onScreen && inPanel;
  }
  function label(el) { return (el.textContent || el.id || "").trim().slice(0, 40); }
  function fire(el, type) { el.dispatchEvent(new Event(type, { bubbles: true })); }
  function type(sel, v) { var el = document.querySelector(sel); if (!el) { return false; } el.value = v; fire(el, "input"); fire(el, "change"); return true; }
  function report(extra) {
    var out = { sc: SC, vw: window.innerWidth, vh: window.innerHeight, errs: window.__errs || [] };
    var dests = Array.prototype.slice.call(document.querySelectorAll("#groups .d"));
    var kinds = Array.prototype.slice.call(document.querySelectorAll("#kinds .b"));
    var must = dests.concat(kinds, [$("save"), $("pagebox"), $("blank"), $("pg_on")]);
    out.nDest = dests.length; out.nKind = kinds.length;
    out.hidden = must.filter(function (e) { return (!$("groupsbox") || $("groupsbox").style.display !== "none") || dests.indexOf(e) < 0 ? !vis(e) : false; }).map(label);
    out.hiddenOther = must.filter(function (e) { return dests.indexOf(e) < 0 && !vis(e); }).map(label);
    out.minBtn = Math.min.apply(null, dests.concat(kinds).map(function (e) { return Math.round(e.getBoundingClientRect().height); }));
    var f = $("fields");
    out.fieldsScroll = f.scrollHeight - f.clientHeight;
    out.cue = !!$("morecue") && $("morecue").style.display !== "none" && vis($("morecue"));
    out.pageScroll = document.documentElement.scrollHeight > window.innerHeight + 1 || document.documentElement.scrollWidth > window.innerWidth + 1;
    out.saveText = $("save").textContent; out.saveOn = !$("save").disabled;
    out.titles = Array.prototype.map.call(document.querySelectorAll("#groups .gt"), function (e) { return e.textContent; });
    out.readFolded = !!$("readbox") && !$("readbox").open; out.readsum = $("readsum") ? $("readsum").textContent : "";
    out.below = dests.filter(function (e) { return !vis(e); }).map(function (e) { var g = e.closest(".grp"); return g ? g.querySelector(".gt").textContent : (e.parentNode.previousElementSibling || {}).textContent || ""; });
    for (var k in (extra || {})) { out[k] = extra[k]; }
    (window.__realFetch || window.fetch)("/result", { method: "POST", body: JSON.stringify(out) });
  }
  function scene() {
    if (SC === "bill") { return report(); }
    if (SC === "receipt") {
      document.querySelector('#kinds [data-k="receipt"]').click();
      var ex = { rcptShown: $("rcpt").style.display !== "none", radios: document.querySelectorAll("#rcpt input[data-rc]").length,
                 pre: (document.querySelector("#rcpt input[data-rc]:checked") || {}).getAttribute ? document.querySelector("#rcpt input[data-rc]:checked").getAttribute("data-rc") : "",
                 filed: $("filedwith").textContent, groupsHidden: $("groupsbox").style.display === "none" };
      document.querySelector('#rcpt [data-mode="rc:cheque"]').click();
      type('#rcpt [data-sv="rc.ref"]', "123456");
      ex.afterMode = $("save").textContent; ex.saveVisible = vis($("save"));
      return report(ex);
    }
    if (SC === "statement") {
      document.querySelector('#kinds [data-k="statement"]').click();
      type('#stmt [data-sv="st.frm"]', "01-05-2031"); type('#stmt [data-sv="st.to"]', "31-05-2031");
      type('#stmt [data-sv="st.total"]', "1300"); type('#stmt [data-sv="st.paid_on"]', "10-06-2031"); type('#stmt [data-sv="st.amount"]', "1200");
      document.querySelector('#stmt [data-mode="st:cheque"]').click();
      var ex2 = { stmtShown: $("stmt").style.display !== "none", ticked: document.querySelectorAll("#stmt input[data-stt]:checked").length,
                  offered: document.querySelectorAll("#stmt input[data-stt]").length, diff: ($("stdiff") || {}).textContent || "",
                  grey: $("stgrey") ? $("stgrey").style.display !== "none" : null, filed: $("filedwith").textContent, saveVisible: vis($("save")) };
      return report(ex2);
    }
    if (SC === "construction") {
      document.querySelector('#kinds [data-k="bill"]').click();
      document.querySelector('#groups [data-d="construction"]').click();
      var e3 = { accShown: $("accbox").style.display !== "none" && vis($("accbox")), accOff: !$("acc").checked };
      document.querySelector('#kinds [data-k="estimate"]').click();
      e3.accHiddenForEstimate = $("accbox").style.display === "none";
      return report(e3);
    }
  }
  var t0 = Date.now();
  (function wait() {
    var h = $("hstamp");
    if (h && h.textContent && h.textContent !== "—" && document.querySelectorAll("#groups .d").length) { return setTimeout(scene, 400); }
    if (Date.now() - t0 > 15000) { return report({ errs: ["the paper did not open in 15 s"] }); }
    setTimeout(wait, 100);
  })();
})();
