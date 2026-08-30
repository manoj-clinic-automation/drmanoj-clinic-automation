# S211_HONESTERRORS — the error popups stop guessing

## Why

30-Aug-2026. The owner tried twice to remove a stray 12-June push from
`https://followup.dr-manoj.in/finance/approvals` and both times the page said

    remove failed — network

so he cleared his cookies, which could never have helped. **The network was fine.**
`mpDismiss` did `r.json()`, and `r.json()` THROWS on any non-JSON reply — a 404
page, or a 500 HTML page. Every such fault fell into a `.catch` whose only word
was "network". The real cause was `S210_DBPATIENCE` never having been installed:
Remove is a *write*, a write that meets a busy database raises
`database is locked`, and that 500 read on screen as a network problem.

**One fault, two victims.** The identical `r.json()` shape sits in `approve()` —
the button used every day to close a day — and in `mgSend()`, the direct Marg
upload. A 500 in either would have read as "network problem" too.

S210 gave Apply honest error popups (`S210_APPLYFEEDBACK`). It did not give them
to the three buttons beside it. This kit finishes that job.

## What changed — five sites, one page, no server file touched

1. **new `srvJSON(r)`** — reads the body once, parses it if it is JSON, and
   otherwise returns the real HTTP status plus the server's own first 180 words.
2. `mpDismiss` (Remove) — uses it; a genuine unreachable server now says so in
   those words, and nothing else is ever called "network".
3. `approve()` — uses it.
4. `mgSend()` (direct Marg upload) — uses it.
5. the two remaining "network problem" alerts renamed to what they mean.

Read-only loaders ("could not load") are deliberately untouched: they carry no
action and no money.

## Proof

- built FROM the pinned live page `2521685e7564e3f4b592b621b3b76de4`
- every anchor asserted by exact count before replacement (1/1/2/1/1)
- `node --check` on the page's script block: OK
- `REHEARSAL_honesterrors.js` runs the SHIPPED bytes of `srvJSON` + `mpDismiss`
  against a seeded 500-lock HTML page, a 404, a JSON 409 refusal, a success and
  a real network reject: **8/8 pass**, including the exact popup the owner saw.

Run the rehearsal from inside this folder:

    node REHEARSAL_honesterrors.js

## Install — after the publish, ONE line on the VPS

    cd /root/deploy/repo && git pull && \cp /root/finance/finance_ui/finance_approvals.html /root/finance/finance_ui/finance_approvals.html.bak_S211_$(date +%Y%m%d_%H%M%S) && \cp deploy_kits/S211_HONESTERRORS/finance_approvals.html /root/finance/finance_ui/finance_approvals.html && systemctl restart clinic-finance.service && sleep 3 && systemctl is-active clinic-finance.service

## Rollback

    \cp /root/finance/finance_ui/finance_approvals.html.bak_S211_* /root/finance/finance_ui/finance_approvals.html && systemctl restart clinic-finance.service
