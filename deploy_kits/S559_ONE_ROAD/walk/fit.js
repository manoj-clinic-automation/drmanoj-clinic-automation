// S559 browser walk -- the bar's fit: how many lines its links take at this window width, and whether the page scrolls sideways.
(function () {
  function report() {
    var bar = document.getElementById("s559bar"), out = { errs: [] };
    if (!bar) { out.errs.push("no bar"); }
    else {
      var links = bar.querySelectorAll("nav a"), tops = {};
      Array.prototype.forEach.call(links, function (a) { tops[Math.round(a.getBoundingClientRect().top)] = 1; });
      var t = bar.querySelector(".s559t").getBoundingClientRect(), n = bar.querySelector("nav").getBoundingClientRect();
      out.items = links.length; out.navLines = Object.keys(tops).length;
      out.barLines = (n.top < t.bottom && t.top < n.bottom) ? 1 : 2;           // the title and the links side by side, or not
      out.barWidth = Math.round(bar.getBoundingClientRect().width);
      out.overflow = document.documentElement.scrollWidth > window.innerWidth + 1;
    }
    (window.__realFetch || window.fetch)("/result", { method: "POST", body: JSON.stringify(out) });
  }
  window.addEventListener("load", function () { setTimeout(report, 300); });
})();
