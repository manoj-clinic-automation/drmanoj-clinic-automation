# S220_REJOIN_RETURNS — one return, counted once

**Ruling behind it (owner, 02-Sep):** *"from 18th June onwards all returns must have item lines… needs a
re-evaluation of the extraction pipeline."* Re-evaluated on the live db copy: since 18-Jun **17 returns**
sit on the bill spine under synthetic `S186-F104-###` references (the S186 backfill, written when that
fortnight's export carried no credit-note bill row) while their item lines sit under the real `CN` number
with no bill row. The audit's union counts each **twice** — "identity needed" + "no patient attributed" —
₹6,559 double-counted, August's return count 47 for 43 real. **Not an extraction gap: a join gap.**
From 17-Aug the daily export carries bill row + lines for every return.

**What it does:** pairs each synthetic row with the orphan credit note of the same day and the same
money (item lines valued through `finance_money`, tolerance ₹10 / 1%), unique both ways, and re-keys
`sale_item.source_ref` to the credit-note number. **Money, patient, day untouched.** Backup beside the
db first; every re-key in `audit_log`; idempotent. Identity stays "identity needed" — that is Darpan's
sheet's job (16 of the 17 had no clinic ID typed at Marg).

**Proven:** dry-run 17 unique · 0 unpaired · 0 ambiguous, every CN and rupee cross-checked against
the owner's full Marg sale-return register; selftest 13/13 on a copy of today's live db (audit rows on
those days 46 → 29; sum of return rupees identical before and after).

**The whole history** (`--from 2026-04-01`): 94 unique · 14 unpaired · 8 ambiguous — the ambiguous are
left alone by design. Not applied by default: D361 accepted the past; the owner decides whether the
metric's baseline should be de-duplicated too.

| file | what |
|---|---|
| `rejoin_returns_s220.py` | the tool — `--dry-run` (default) / `--apply` / `--from` |
| `selftest_rejoin_s220.py` | 13 checks on a copy of the db |
