# S638 anchored edits for /root/finance/finance_ui/finance_approvals.html (FROM b32da7ff)
# D780: a Needs-you line that carries href opens that page (the expiry watch); the page's links row gains "Expiry watch".
EDITS = []
EDITS.append(('''      return '<li onclick="goSec(\\''+esc(l.target)+'\\')"><span class="dot '+esc(l.cls||"warn")+'"></span>'+esc(l.text)+act+' <span class="mut">▸</span></li>'}).join("");''',
              '''      var go=l.href?'location.href=\\''+esc(l.href)+'\\'':'goSec(\\''+esc(l.target)+'\\')';   /* S638 (D780): a line with href opens its own page */
      return '<li onclick="'+go+'"><span class="dot '+esc(l.cls||"warn")+'"></span>'+esc(l.text)+act+' <span class="mut">▸</span></li>'}).join("");'''))
EDITS.append(('''  <a class="ext" href="/finance/workbench">Yes Bank statement · load and reconcile ↗</a> ·''',
              '''  <a class="ext" href="/finance/sanjeevni/expiry">Expiry watch ↗</a> ·
  <a class="ext" href="/finance/workbench">Yes Bank statement · load and reconcile ↗</a> ·'''))
