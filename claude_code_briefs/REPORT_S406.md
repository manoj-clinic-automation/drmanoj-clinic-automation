# REPORT_S406 — S406_RETURNS_TWO_KINDS (the Returns section: counter returns vs your non-cash returns)

Installed on srv1746119 on **26-Sep-2026**, installer stamp 08:41:30 IST, done 08:46:18 IST, verified 08:46:55 IST (times read from
the log and the probe). Every pin re-read live first (08:24 IST, after S405). Published with PUBLISH_ALL.bat.

## For Dr Manoj (plain English)
- **September, before and after.** The Returns card read *30 returns · ₹12,427 · 13 need your OK*. It now reads **Counter returns —
  29 · ₹9,257 · 1.9% of counter sales**, with August beside it in grey, and **Your non-cash returns — 1 · ₹3,170** as its own collapsed
  block (that is CN00208 of 11-Sep, the home-medicine credit note: goods back, no cash — it no longer counts as a counter refund).
  **Need your OK: 13 → 4.**
- **A minor discount is no longer a finding.** A difference under ₹20, or under 2% of the return, reads plain *ok*; the paise are still
  inside the line when you tap it. What needs you now is only a counter return of ₹1,000 or more, an item the patient never bought, or
  more returned than sold — and only until you decide it. Your own non-cash returns are never asked.
- **One clean line per return:** bill · date · patient · amount · one word (*ok*, *your OK*, *never bought*, *over-refund*,
  *discounted*, *unchecked*, *large*, *rejected*). All the audit text is inside the tap-open line, unchanged. If the server classes
  a return wrongly, one tap inside the line flips it ("mark as my non-cash return" / "mark as counter return") and your word is kept.
- **The Month table** gains a *returns* column: the counter-return % and rupees for each month. The Needs-you line uses the new count.
- The old card is one link away ("old view"). Approvals you already gave stay. No money figure, day figure, cash or Marg reconciliation
  changed. Proved on a copy of the live database with crafted credit notes; the live data was not written.
- **https://followup.dr-manoj.in/finance/approvals**

## For the chat
### September (live data, read-only through the new API on the scratch copy, 08:41 IST)
| | before (old rule) | after (S406) |
|---|---|---|
| returns · total | 30 · ₹12,426.85 | 30 · ₹12,426.85 (unchanged) |
| counter returns | — | 29 · ₹9,256.85 · **1.9%** of counter sales (₹4,77,312) |
| your non-cash returns | — | 1 · ₹3,170 (CN00208, "the credit note's own text names a home-medicine bill") |
| need your OK | 13 | **4** |
| status words seen | — | discounted · large · ok · unchecked · your OK |

### Live files FROM → TO (md5 read back after placing; re-read 08:46 IST identical)
| file | FROM | TO |
|---|---|---|
| /root/finance/darpan_app.py | 2c22822d49a20143058b5d781eb3c06e | 5bfabbecf1e0fbf86ff142e3cd07543e |
| /root/finance/sanjeevni_approvals.py (S405's TO; v1.6 → v1.7) | 126f90fc9912092378e817f101a8f74e | 74fe5437afd646851d0c28200592177d |
| /root/finance/finance_ui/finance_approvals.html (S405's TO; clinic — declared) | 928a25ef503267ce8e518f126306c236 | 77c79211845f3416a3211d22ced3d7db |

New: `/root/finance/returns_kinds.py` bd45cfebbaad8ab4f909d025f8b6f948. Built on the box by `make_s406.py` from the live bytes
(anchored edits, each exactly once); TO pins matched the kit. `cn-approve`, `finance_returns_audit`, `sanjeevni_cash`, the day and
cash paths: untouched.

### What the kit does (the design decisions, for the record)
- `cn_kind` (unit, bill_no, kind, why, source auto|owner, decided_at, by): classified on read while the month is open (the current
  month, or one with an unapproved day); the owner's flip is kept. The classifier's ladder: the credit note's own text (review-queue
  JSON / identity tables — S399's method) → the S357 cash adjustment naming it → the patient's own bill in the window being a
  home / procedure (`day_noncash_bill`) or ruled (`cash_bill_ruling`) bill → else counter.
- Status words: the brief's five plus **discounted** (a SHORT refund is not an over-refund) and **unchecked** (the audit could not run —
  a question, not a finding). The over-refund difference is the per-pack excess the audit names on its lines; the discount
  difference is gross − net.
- Need-your-OK: counter returns only, from `returns.act_from` (S219), amount ≥ `returns.big_p` (new setting, seeded ₹1,000 — S220's
  `returns.large_p` stays for the old renderer) or NEVER BOUGHT / RETURNED MORE THAN SOLD, undecided. A line the old rule asked about
  and the new does not keeps "approve anyway" in its detail.
- The %: counter returns ÷ (sale − home − procedure bills) from `sanjeevni_cash.month_rows` — the same figures as the Month table.
- `NEEDS_YOU_WITHOUT_S406=1` keeps the old Needs-you count; set ONLY by S400's frozen walk re-run, as S403's switch is.

### Backups · services · health · data
`/root/finance/finance.db.bak_S406_20260926_084130` · `darpan_app.py.bak_S406_2c22822d` · `sanjeevni_approvals.py.bak_S406_126f90fc` ·
`finance_ui/finance_approvals.html.bak_S406_928a25ef`. Restarted `clinic-finance` only (active; portal, assetapp untouched). healthz 200;
`/finance/approvals` and cn-detail 302 to a plain curl (login gates, expected); journal clean. Seed: `returns.noise_p` 2000 ·
`returns.noise_pct` 2 · `returns.big_p` 100000 (INSERT OR IGNORE). At 08:46 IST `cn_kind` did not exist yet (first owner read makes it);
no W406 rows on the live database — the walk's writes stayed on the scratch copy.

### The walk (walk_s406.py — the real finance app over a scratch copy)
`WALK_S406 GREEN -- 27/27` (full output in this session's log): the real month read first (the table above; CN00208 noncash) · eight
crafted notes W406CN1–8 on 25-Sep against a crafted prior sale of 24-Sep: a HOME MEDICINE text → noncash / unchecked, not asked though
₹1,500 · a ₹12 discount → ok, not asked · a ₹80 discount on ₹1,420 → your OK · a never-bought ₹300 → your OK · an orphan named from
its kept bill text · a ₹5 over-refund → ok · a ₹38 over-refund → over-refund, not asked · the patient's own home bill → noncash ·
Need-your-OK +2 where the old rule gives +8 · sums (+₹3,837 counter / +₹2,300 non-cash) · the % to the tenth against the month row ·
the flip (darpan 403, bad kind 400; audited; kept over recompute) · cn-approve still works · the Needs-you line (new 5 / old rule 20)
· the months API fields · the gate · timing: cn-detail ~0.4–0.5 s, needs-you ~0.3–0.4 s, months ~0.4 s.
**Negative controls (the old files, the same crafted notes):** no kinds, the ₹12 rounding one counted, Need-your-OK +8, the old count on
the line, no column, no renderer. **Re-runs:** `WALK_S405 29/29` · `WALK_S404 65/65` · `WALK_S403 52/52` · `WALK_S400 63/63` · `WALK_S402 16/16`
(S400's with both env switches). One earlier installer run went red on the walk's own expectation (the old-rule count also drops by one
after an approval) — corrected in the walk; nothing was placed by that run.

### Outside the brief, noticed (not changed)
- 25 of September's 29 counter returns read *unchecked* or *ok* only because the audit could not run (no patient, identity needed);
  the *unchecked* word says so on the line now. Naming the patients on those bills (the review queue) would make them auditable.
- The approvals page now scans the month's returns three times per load (the card, the Needs-you line, the Month table) at ~0.4 s each.
  Fine today; a cache is the fix if it ever drags.

### Kit
`deploy_kits\S406_RETURNS_TWO_KINDS\` — returns_kinds.py, make_s406.py, seed_s406.py, walk_s406.py, install_S406_RETURNS_TWO_KINDS.sh,
README.md, KIT_ID.txt, SUMS.md5. Ran from `/tmp/s406kit/S406_RETURNS_TWO_KINDS` (md5sum -c OK; sibling kits linked from the clone); the
repository copy is byte-identical (verified after `git pull`). No `__pycache__`. NO_PHONE_NUMBERS gate: clean. Build lock held from
08:40 IST to the publish, then removed.

### Undo
Put back the three `.bak_S406_<from8>` files, remove `returns_kinds.py`, `systemctl restart clinic-finance`, healthz 200, md5s read back.
`cn_kind` and the settings are data and harmless; `finance.db.bak_S406_20260926_084130` only if the owner asks.
