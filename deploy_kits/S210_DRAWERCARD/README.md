# S210_DRAWERCARD — Darpan sees what his drawer SHOULD hold

## The owner's requirement (30-Aug-2026, his words)

> "I need to know what darpan holds in his drawer **and he should know what he should be
> having there**."

Until now Darpan's card showed only the single day. His expected drawer existed on no screen
of his — while the owner console told the owner. All of August's takings (₹3,20,340) went
unbanked partly because the person who does the banking was never shown a number or a nudge.

## What this adds — ONE file, page-only, no server code, no restart

A "Drawer mein hona chahiye" section above the evening-count box, in the page's own
Hindi-first voice:

- **expected drawer** (₹26,182 today) from `/finance/api/cash-position` — the SAME endpoint
  and arithmetic as the owner console (its docstring: serves maker and checker alike);
- dated honestly: "(2026-08-27 tak ke hisaab se — aaj ki sale ismein nahin hai)". The evening
  count includes today's takings, so the two figures sit side by side and are NEVER
  auto-compared into a false alarm;
- **the bank nudge**: "Aakhri bank deposit: 2026-07-30 · 31 din pehle ⚠ bank jaana hai",
  red past 15 days — the alarm whose absence let a month of cash pile up;
- a collapsed "roz ka hisaab" day table (drawer + unbanked, last 14 filed days).

## Proof

- Base: `S208_DARPAN/darpan_card.html` (`977cc93bb4ca…`, the live pin); edits anchored,
  refused if ambiguous.
- **js_gate (S209): PASS.**
- **Walk under node, server-true fixture (the same one v2 of S210_ONEMONEY proved, and the
  owner's live look confirmed): 5/5** — ₹26,182 shown, caveat dated, red 31-din nudge,
  day table, and an honest "load nahin hua" when the API refuses.

## Install — VPS, one line at a time

```
git -C /root/deploy/repo fetch --depth 1 origin main && git -C /root/deploy/repo reset --hard origin/main
```
```
\cp /root/finance/darpan_card.html /root/finance/darpan_card.html.bak_S210_$(date +%Y%m%d_%H%M%S)
```
```
\cp /root/deploy/repo/deploy_kits/S210_DRAWERCARD/darpan_card.html /root/finance/darpan_card.html
```

No restart — pages are read from disk per request. The walk is one look at
https://followup.dr-manoj.in/finance/darpan (as Darpan or yourself): the new section sits
above "Aaj shaam ki ginti".

⚠ If the live `darpan_card.html` is NOT `977cc93bb4ca…`, STOP and tell Claude — the kit was
built from the S208_DARPAN bytes and must be rebuilt from what is actually live.
Check: `md5sum /root/finance/darpan_card.html`

*S210 · 30-Aug-2026.*
