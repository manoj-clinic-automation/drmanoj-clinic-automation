# S195_ENTRY — /finance/entry redirects to the live page (v2)

Old /finance/entry (typed/bookmark) showed the outdated single-page screen.
Now it redirects by role: maker -> /finance/daily (v2), checker -> /finance/review.
Old page kept ONLY at /finance/entry?legacy=1 . One file changed (finance_app.py);
the 4 selftest fetches that assert the old page body were repointed to ?legacy=1
so SMOKE stays all-green; the 2 redirect-behaviour selftests are unchanged.

Live path: /root/finance/finance_app.py . Currency-gated to S194E (d2863c30...).
Backs up, py_compiles, runs --selftest (all-green, not shrunk), restarts
clinic-finance, auto-rolls-back on any red. New md5: 85df28fea117f8fc977b319cdfe70631 .

Install:
  cd /root/deploy/repo && git pull
  cd deploy_kits/S195_ENTRY && bash install_s195_entry.sh
