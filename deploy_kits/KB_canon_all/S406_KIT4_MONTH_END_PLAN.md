# S406 — KIT 4, THE MONTH END (kit S750_MONTH_END) — the plan and the owner's rulings — 08-Nov-2026

*The Sanjeevni chat, session 406. Kit 4 of `S391_PURCHASE_RECONCILE_PLAN.md` §4 (D849, F-1175), taken before F-802's fix on the owner's word (08:58 IST; D867's order revised). Kit number S750 and the PLANNED line for the Scan App's two files taken on `board/_numbers` at v1066. The mock (artifact *Kit 4 Month-End Mock*, v2) approved 09:45 IST.*

## 1 · The owner's words this session

- **09:24** — the word is **summary**, not statement (*Dealer summaries*; the tick *Dealer ka mahine ka hisaab (summary) hai*).
- **09:24** — our own statement is **not sent to the dealers routinely**. It is kept in the system as the **dealer ledger** — all the data is there (bills with items, payments) — accessible and printable when needed.
- **09:45** — *All ok.* The ledger has the **monthly reconciliation built in**, **months collapsed and expandable**, **each bill's item lines collapsed and expandable**, and **item quantities supplied per dealer — monthly and for the financial year** (April–March).

## 2 · What kit S750 builds

| # | what | file |
|---|---|---|
| 1 | **Reception's tick** on the pharmacy lane, beside the challan tick: *Dealer ka mahine ka hisaab (summary) hai — bill nahi*. The scan lands as `kind='Summary'`, `doc_kind='summary'` (as a challan lands as `kind='Challan'`), so the register never takes it for a bill scan. The slip: *Summary liya ✓*. | `assetapp/asset_register.py` (the Scan App's — PLANNED) |
| 2 | **The reader's second prompt** `read_summary()`: dealer, period, every bill line (number · date · amount), credit notes, the closing total → `claude_reading` with `doc_kind='summary'`; called for `kind='Summary'` where `read_bill` is called today. | `assetapp/claude_reader.py` (the Scan App's — PLANNED) |
| 3 | **Row 7 — Dealer summaries**: one line per dealer of the month — the summary's figure against Marg's bills less Marg's purchase returns; *Agrees ✓* to the rupee, else the per-bill *why* (a bill on the summary not in Marg · a bill in Marg not on the summary · an amount that differs · a credit note). A difference already explained by row 2 (paper ≠ Marg) or row 6 (a return) says so and holds nothing new. *Awaited* with *Ask reception to scan it* and *Gives no summary* (a standing word per dealer, Undo). An owner-confirmed dealer (row 3) — his *Confirm* counts as the summary. | `scan_register.py` (S750 section: `s750_*`; row 7 replaces the grey placeholder in `s749_rows`) |
| 4 | **The owner's answers** on an unexplained line (a bill on the summary we do not have; an amount only the dealer has wrong): *Ask the dealer* (waits, *asked dd-mm*) · *Carry to next month* (the amount shows under next month's *Carried in*; this month stops waiting) · *Accept* (the dealer's figure stands on the sheet; a card tells Amir to enter the bill when the paper comes). Every answer audited with Undo (`s750_act`). Nothing here sends a message or taps anything for him. | `scan_register.py`, `amir_day.py` (the card) |
| 5 | **Row 8 and the lock** (D849): opens when rows 2–7 are clear and Marg's re-export dated **after the last correction** is in — that re-export is the proof the corrections went in. Marg's two statements are no longer compared with each other. `s749_month_open` / `s749_lock_reasons` keep their keys and words (the parent's `month_read.py` reads them) and gain the dealers' holds — the parent is told at the close. | `scan_register.py`, `purchase_app.py` (`_lock_gate` wrapped once more) |
| 6 | **The payment sheet**: a *Dealer's summary* column (the figure · *agrees* / *differs* / *awaited* / *none given*); **Payable follows the dealer's figure** once the line agrees or is accepted; a carried amount appears under next month's *Carried in*. The owner's typed values are never rewritten. | `purchase_app.py` (`_pay_rows`, `_pay_sheet_table` wrapped) |
| 7 | **The dealer ledger** `/finance/purchase/page/ledger` (the dealers) and `/page/ledger/<dealer>`: the financial-year block first (purchases · returns · paid · balance; **items × quantity for the FY**), then **one month per fold** (newest open): the bills (each bill's **item lines folded**), the returns, the dealer's summary and its verdict, the payments (NEFT with the bank's reference, cheques) and the balance; **item quantities for the month**. Read-only; printable (`@media print` opens every fold). Reached from row 7, the sheet and the hub. | `purchase_app.py` |
| 8 | **Reception's list** (*Aaj ka bill kaam*): *<Dealer> ka <month> ka hisaab (summary) scan karo* after the owner's *Ask reception to scan it*; *Dobara scan karo* when a summary could not be read. | `porders.py` |

**Not touched:** Amir's *Aaj ka kaam* list (D690); the expiry page; the spine; the medical PC; `assets.db` stays READ ONLY on the finance side (the summary is read from `claude_reading`, the scan shown by the asset app's own image route).

## 3 · Proof

`py_compile` → the walk on a made-up root in the device VM (a month with four dealers: one agrees, one differs by a return explained by row 6, one with a bill we do not have, one awaited; the owner's three answers and their Undo; the lock opening only when all is clear and the re-export is dated after the last correction; the ledger's FY and month totals equal to the bills' lines) with a CONTROL that goes red → `proof_s750.py` run by the live files and by the kit's → a cold review until SAFE → the installer rehearsed on a made-up root with stubs → SUMS last → placed → his publish → his one server line (no DRY needed: nothing live is re-paired or re-stated — new tables only) → the screens read live as `manoj` by a sub-agent.

*S406_KIT4_MONTH_END_PLAN · the Sanjeevni chat · 08-Nov-2026 · nothing live changed by this paper.*
