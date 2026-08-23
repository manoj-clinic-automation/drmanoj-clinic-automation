# S195 — Everything pending (UPDATED at chat close, 22-Aug-2026)

Supersedes the morning version of this doc. Clubs 1–2 largely executed; state below is
verified against what actually shipped, not what was planned.

---

## DONE this chat (do not redo)

- **Correction checklist** live and self-closing (`/finance/marg-worklist`), floored at
  `FINANCE_CORRECTION_FROM=2026-08-01`, with Excel (Yes/No dropdown) / WhatsApp / email /
  CSV handover. Live pin `df75024392e31ae99bb3fde9fab24062`, smoke **654/654**.
- **Club 2 entire**: Darpan's accuracy on portal tile + in save response; email agent
  folded/encoded subjects fixed; A4 month check + never-filed days on health page;
  pre-flight sweep extended to portal.py and email_agent.py.
- **GAS backfill**: 163 statements loaded (medical 56, clinic 55, lab 50, back to 06-Jun);
  daily window widened to 10 days. Verdict: split wrong on only 1 day since 1-Aug (₹30,
  06-Aug) — Darpan works accurately.
- **18-Aug corrected and approved at 25,176** (partial 22/30-bill export was the cause);
  **20-Aug approved**; **21-Aug push applied**.
- **Credit-note sign fault** fixed in all three readers via `marg_net_sql()`.
- **Publishers hardened** (stale-git-lock sweep in both PUBLISH bats).
- **Auditor ideated and seeded** → `claude/AUDITOR_SEED_v1.md`, continues in its own chat.

## STILL OWED — owner, ~15 minutes

1. **Rotate `FINANCE_MARG_TOKEN` + `FINANCE_CRON_TOKEN`** (cron token also in GAS Script
   Properties of project "UPI Reconciliation"). Printed in chat during the 401 crisis.
   **Aging since 21-Aug. Highest-severity open item in the estate.**
2. **17-Aug ₹20,000 → Staff Ledger** (recover 8k from Aug salary, then 4k/month, against
   the scanned application). Drawer reads 175,201 only after this: 193,904 + 1,297 − 20,000.
3. **8 bills, ₹4,577, in 18-Aug's review queue** — patient attribution only, money already
   correct. `/finance/approvals` → 18-Aug.

## STILL OWED — builder, next sessions

- **Club 3** (needs one sample export each, dropped in margsync): purchase, supplier-wise,
  stock, purchase-register, Labmate, Docterz → router signatures.
- **Club 4** (needs three answers in one message): monthly bank statement details for Amir;
  accountants' emails + Tally export source/due-day; **how Amir gets files onto the medical
  PC** — the answer that unblocks the most.
- **Viewer for expense / no-payment-bill scans** — evidence is compulsory and recorded but
  has NO route to open it (two routes mirroring `api_attachment` + links where ticks show).
- **Entry page: say WHY File day is disabled** (the silent-gate UX that cost a round trip
  during the 18-Aug correction).
- Repo copy of `finance_entry.html` is **stale vs live** — refresh the mirror (doc-drift;
  also flagged to the auditor).
- Club 5 unchanged: NEFT assembly (assemble/file only, never send), S195_DBPULL (SSH key +
  passphrase decision), AHK (one-line version check), covering-letter template.
- Amir's correction schedule + Darpan-side sharing of the daily difference list — waiting
  on Amir's editing schedule being fixed.

## Standing lessons adopted this chat

- Pre-flight before any kit: `py_compile` → `pyflakes` → `check_late_locals.py` →
  `check_row_keys.py` (all in `tools/`).
- **Never assert against a shape not printed in this session** — five rollbacks, one habit.
- Hand-written record vs computed figure → **regenerate from source** before believing
  either (the 23,879 screen vs the 25,176 paper).
- No git commands from the Cowork sandbox against the mounted repo (index.lock is
  undeletable from there; publishers now self-clear stale locks).
