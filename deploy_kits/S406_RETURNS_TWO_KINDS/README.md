# S406_RETURNS_TWO_KINDS — the Returns section of the approvals page: counter returns vs the owner's non-cash returns

**Sanjeevni project · session 283 · 26-Sep-2026 · decision D622. Second of the five-brief paste, after S405.**
A read-only redesign of one section plus two categories: **no money figure, day figure, cash or Marg reconciliation changes.**

## What the owner asked for (26-Sep)
"Check the Returns section of the approvals page. Remove the lines where the difference is a minor discount. Flag my own
non-cash returns separately. Show what percentage of counter sales is returned at the counter."

## What was built
**NEW `/root/finance/returns_kinds.py`** — a read layer over `finance_returns_audit` (the S212/S213 engine) and darpan_app's
cn-detail. It owns one table `cn_kind` (unit, bill_no, kind, why, source auto|owner, decided_at, by) and three settings.
1. **Two kinds.** Every credit note is `counter` or `noncash`. `noncash` when the credit note's own text names a home / procedure
   bill (the word lists `noncash.home_words` / `noncash.proc_words`, read from the review queue's kept JSON and the two identity
   tables — S399's method), or the S357 cash adjustment names the credit note, or the patient's own bill in the window is a
   home / procedure bill (`day_noncash_bill`) or a ruled one (`cash_bill_ruling`); else `counter`. Stored once, recomputed on read
   while the month is open (the current month, or a month with an unapproved day); the owner's flip (`POST /finance/darpan/api/cn-kind`,
   owner only, audited in `darpan_audit`, source `owner`) is kept over every recompute.
2. **Headline:** `Counter returns — N · ₹X · x.x% of counter sales`, last month beside it in grey. `Your non-cash returns — N · ₹Y`
   as a collapsed block; **they never enter the counter %**. The % = counter returns ÷ (the month's sale − home − procedure bills),
   the figures `sanjeevni_cash.month_rows` already gives the Month table.
3. **Rounding is not a finding.** A `DISCOUNTED RETURN` (gross − net) or a `REFUNDED MORE THAN PAID` (the per-pack excess the audit
   names on its lines) whose difference is below `returns.noise_p` (setting, default ₹20) **or** below `returns.noise_pct` (setting,
   default 2 %) of the return reads `ok`; the paise stay inside the tap-open detail ("below the rounding line — not a finding").
4. **One clean line per return:** bill · date · patient · amount · ONE status word. The set is `ok · never bought · over-refund ·
   discounted · unchecked · large · your OK · rejected`. The brief named five; the data forced two more: **`discounted`** (the refund
   was SHORT of the goods' worth — a different fact from an over-refund) and **`unchecked`** (the audit could not run: no patient
   attributed, identity needed / disputed, no lines — a question, never a finding). All audit text (population, money-from, verdict,
   lines found by, the line table) is inside the tap-open detail, unchanged words.
5. **"Need your OK" counts only real items:** counter returns from `returns.act_from` (S219) with amount ≥ `returns.big_p` (setting,
   default ₹1,000) or `NEVER BOUGHT` or `RETURNED MORE THAN SOLD`, undecided. The owner's own non-cash returns are his and are not
   asked. `cn-approve` is untouched; an approved item stays approved and reads `ok ✓ approved`. A line the old rule asked about and
   the new one does not still offers "approve anyway" inside its detail, so nothing is lost.
6. **Patients for the orphan returns** through the kept bill text (`identity_resolution` / `identity_dispute` / the review queue's
   JSON) — shown as "patient (from the bill text)".
7. **Month table** (`/finance/sanjeevni/api/months`) gains `counter_returns_n / _p / counter_returns` (rupees) / `counter_returns_pct`;
   the table shows a **returns** column (% and rupees).
8. **Needs you:** `N return(s) of ₹X need your OK` uses the new count (`returns_kinds.pending_count`). `NEEDS_YOU_WITHOUT_S406=1`
   keeps the old rule — set ONLY by S400's frozen walk re-run (it asserts Needs you unchanged); the service never sets it.
9. **The old renderer** is kept byte-for-byte as `loadCNOld()` and is one link away ("old view") on the card; the spot-count list
   (S220) is drawn by both.

`returns.large_p` (S220's gate, ₹1,000) stays for the old renderer; `returns.big_p` is the S406 rule's own setting, seeded at the
same ₹1,000.

## Pins (FROM read on the box 26-Sep-2026 08:24 IST, after S405 → TO; built by `make_s406.py` from the live bytes)
| file | FROM | TO |
|---|---|---|
| /root/finance/darpan_app.py | 2c22822d49a20143058b5d781eb3c06e | 5bfabbecf1e0fbf86ff142e3cd07543e |
| /root/finance/sanjeevni_approvals.py (S405's TO; v1.6 → v1.7) | 126f90fc9912092378e817f101a8f74e | 74fe5437afd646851d0c28200592177d |
| /root/finance/finance_ui/finance_approvals.html (S405's TO; clinic — declared) | 928a25ef503267ce8e518f126306c236 | 77c79211845f3416a3211d22ced3d7db |

Restarts `clinic-finance` only. `finance.db` is backed up first; the seed adds three settings (INSERT OR IGNORE). `cn_kind` is made on
first use. No finance_app / portal / grants change.

## Proof
`walk_s406.py` — the REAL finance_app over a SCRATCH copy of finance.db: the real month read first, read-only (CN00208 classes
noncash; Need-your-OK under the new rule ≤ 6; every line's status word from the set) · eight crafted credit notes keyed W406* in the
current month (a HOME MEDICINE text → noncash, unchecked; a ₹12 discount → ok; a ₹80 discount on ₹1,420 → your OK; a never-bought
₹300 → your OK; an orphan named from its kept bill text; a ₹5 over-refund → ok; a ₹38 over-refund → over-refund, not asked; a return
against the patient's own home bill → noncash) · Need-your-OK grows by exactly 2 where the old rule grows by 8 · the counter and
non-cash sums · the % to the tenth against sanjeevni_cash's own month row · the owner's flip (darpan 403, bad kind 400), audited,
kept; cn-approve still works · the Needs-you line new vs old rule · the months API fields · the gate. **Negative controls** on the
box as it is with the SAME crafted notes: no kinds, the ₹12 rounding one counted, the old count, no column, no renderer. Then
**S405's, S404's, S403's, S400's and S402's own walks re-run** on the patched files (S400's with both env switches).

## Run
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S406_RETURNS_TWO_KINDS/install_S406_RETURNS_TWO_KINDS.sh
```
Undo: put back the three `.bak_S406_<from8>` files, remove `returns_kinds.py`, `systemctl restart clinic-finance`, healthz 200.
`cn_kind` and the settings are data and harmless; the database backup is used only if the owner says so.
