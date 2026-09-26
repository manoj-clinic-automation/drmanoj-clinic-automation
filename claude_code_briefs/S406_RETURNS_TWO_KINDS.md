# Claude Code brief — S406_RETURNS_TWO_KINDS (the Returns section of the approvals page: counter returns vs the owner's non-cash returns)

Written 26-Sep-2026 by the Sanjeevni chat (S283). Read `CLAUDE.md` first. **Kit S406 · decision D622.** The owner approved this WHAT
on 26-Sep. Runs SECOND in the paste, after S405 is installed and published. Read-only redesign of one section plus two categories:
**no money figure, day figure, cash or Marg reconciliation changes.**

## 1 · The owner's words (26-Sep)
"Check the Returns section of the approvals page. Remove the lines where the difference is a minor discount. Flag my own non-cash
returns separately. Show what percentage of counter sales is returned at the counter." Plan approved as written in §3.

## 2 · What exists (all `/root/finance/`)
- The card `#returnsCard` on `/finance/approvals` (`finance_ui/finance_approvals.html`, **c319bb56 after S403 — read live**) is filled by
  `GET /finance/darpan/api/cn-detail?month=YYYY-MM` in `darpan_app.py` (2c22822d) and approved through `POST /finance/darpan/api/cn-approve`.
  Each line today carries audit words (population, money-from, lines found by) and a verdict from the MONEY_FLAGS set
  (`NEVER BOUGHT`, `REFUNDED MORE THAN PAID`, `RETURNED MORE THAN SOLD`, `DISCOUNTED RETURN`) — `darpan_app.py` ~1202, `darpan_kal.py` 54.
  September live: 30 returns ₹12,427, "13 need your OK"; 5 DISCOUNTED RETURN and 2 REFUNDED MORE THAN PAID are ₹1–₹15 rounding;
  CN00208 of 11-Sep ₹3,170 is the HOME MEDICINE credit note (goods back, no cash, D594/S357) counted today as if a counter refund.
- Credit notes: `sale_bill.is_credit_note`; their bill text; the label words in `setting` (`noncash.home_words`, `noncash.proc_words`,
  S356/S399) and the rows in `day_noncash_bill` / `cash_bill_ruling`; the credit-note cash adjustment row S357 writes (`cash_adjustment`).
- "No patient" on three returns only because their bill sits in the review queue: S399's method — the bill text kept in
  `identity_resolution` / `identity_dispute` / `sale_item_review` names the patient.
- Counter sales for the % : the month's sale (Marg bills) minus the non-cash (home/procedure) bills — the same figures `sanjeevni_day.py`
  (22a38006) / the Month table (`/finance/sanjeevni/api/months`, `sanjeevni_approvals.py` 675aab4a — read live) already compute.

## 3 · The build (D622) — the API gains fields; the card is re-rendered; the old renderer stays reachable one link away
1. **Two kinds.** Every credit note is classed `counter` or `noncash`: `noncash` when its original bill is a home/procedure bill (by the
   same word lists, or a `day_noncash_bill` / `cash_bill_ruling` row); else `counter`. Stored once per credit note in a new table
   `cn_kind` (bill_no, kind, why, decided_at) recomputed on read only while the month is open; the owner may flip a kind with one tap
   (audited, `cn_kind.by`).
2. **Headline:** `Counter returns — N · ₹X · x.x% of counter sales` for the month, and the same for last month beside it.
   `Your non-cash returns — N · ₹Y` as its own collapsed block; **they never enter the counter %**.
3. **Rounding is not a finding.** A `DISCOUNTED RETURN` / `REFUNDED MORE THAN PAID` whose difference is below `returns.noise_p`
   (setting, default ₹20) **or** below `returns.noise_pct` (setting, default 2 %) reads `ok`; the paise stay inside the tap-open detail.
4. **One clean line per return:** bill · date · patient · amount · one status word (`ok` · `never bought` · `over-refund` · `large` ·
   `your OK`). All audit text moves inside the tap-to-open detail (unchanged words, so nothing is lost).
5. **"Need your OK" counts only real items:** amount ≥ `returns.big_p` (setting, default ₹1,000) or `NEVER BOUGHT` or `RETURNED MORE
   THAN SOLD`. Expected September: 13 → about 5. Approved items stay approved (`cn-approve` untouched).
6. **Patients for the orphan returns** through the kept bill text (S399's lookup, reused — import, do not copy).
7. **Month table** (`/finance/sanjeevni/api/months`) gains `counter_returns_p` and `counter_returns_pct`; the table shows the % column.
8. The **Needs you** line `N sale return(s) need your decision` uses the new count.

## 4 · FROM pins (read live first; mismatch = stop that file and report)
| file | FROM |
|---|---|
| /root/finance/darpan_app.py | 2c22822d49a20143058b5d781eb3c06e |
| /root/finance/sanjeevni_approvals.py | 675aab4a46ab8792f05b17cab15d17ee (as S405 left it — read live; the months API only) |
| /root/finance/finance_ui/finance_approvals.html | as S405 left it — read live (clinic — declared; the returns card + one Month column) |
No `finance_app.py`, portal or grants. Restart `clinic-finance` only.

## 5 · The walk (scratch copy; own credit notes keyed W406*; the real September as a read-only check)
A home-medicine credit note classes `noncash` and is absent from the counter figures · a plain one classes `counter` · the owner's flip is
stored and audited · a ₹12 DISCOUNTED RETURN reads `ok` and is not in Need-your-OK; a ₹1,420 one is · NEVER BOUGHT is, whatever the amount ·
the % equals counter returns ÷ (sale − non-cash bills) for the month, to the paisa on the crafted month · the orphan lookup names a patient
from a crafted `identity_resolution` row · the months API carries the two new fields; older months unchanged · cn-approve still works and an
approved item stays approved · real September (read-only): CN00208 classes noncash, Need-your-OK ≤ 6 · negative control: the old files ·
S400/S402/S403/S404/S405 walks re-run green.

## 6 · Done means
Kit `deploy_kits\S406_RETURNS_TWO_KINDS\` · installed, md5s read back · healthz 200 · published · `claude_code_briefs\REPORT_S406.md`
(owner lines first: the September figures before and after — count, total, %, need-your-OK; ending with
`https://followup.dr-manoj.in/finance/approvals`). Then go on to S407.
