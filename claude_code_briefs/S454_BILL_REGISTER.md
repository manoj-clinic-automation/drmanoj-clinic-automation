# Claude Code brief — S454_BILL_REGISTER (every Marg purchase bill of a month on one register with its paper: verified only on what the scan reads well, items judged by Marg's own arithmetic and by learnt names, a missing scan as a re-upload line that reaches a person, the month reading "N of N")

Written 02-Oct-2026, 22:4x IST, by the Sanjeevni chat (S283 post-close), at the owner's word: "go. But do not build or code anything right now." **It is built only when the owner pastes its line.** Read `CLAUDE.md` first. **Kit S454 · decision D662 · faults F-690, F-691** (System Board `_numbers` v179). It serves D650 (Marg's entry is final; the scan is the witness), D640 (everything the scan flow needs from a person is a one-tap line in the staff's own list) and D648 (every duty has a door).

**Runs AFTER S452_AMIR_PANEL_FIXES is installed, on its TO pins.** If `claude_code_briefs\REPORT_S452.md` does not exist, stop and say so.

**Touches (declared, all Sanjeevni's):** `/root/finance/purchase_app.py`, `porders.py`, `porders.html`, `reports_tile.py`, `sanjeevni_approvals.py`; `amir_day.py` only if the corrections list needs a new line kind; `claude_code_briefs/DUTY_MAP.md` + `.json`. **READ ONLY:** the asset app's store (through `purchase_app`'s existing door), `item_alias.py`, `packs.py`. **No parent file:** not `finance_app.py`, `portal.py`, `tile_grants.json`, `finance_approvals.html`, `asset_register.py`. If a parent file turns out to be needed, stop and report; do not edit it.

## 1 · How this came

On 02-Oct the owner asked what the net result is of September's bills: staff scanned the papers, Amir keyed every purchase into Marg, the exports reached the server. The chat read his live pages and answered: not whole. His words that this brief serves:

- "These three fields are being cached correctly. Because if it is so, then we can cross verify what bills with Marg have been verified. Because reading the item data must be an issue."
- "Our system mainly verifies the verifiable fields with the cross checks that these bills have arrived, and what all bills are missing should be populated for re-upload."
- "We should consider only the data which we can verify, and the other data we should find a way how to match it properly with our data."
- "The Marg system accepts a photo and a PDF, both." So the files S446 serves to Amir for Marg's digital entry need no conversion; that route stays as it is.

## 2 · What the chat read on the live pages, 02-Oct ~22:00 IST — REPORT the same facts first, as they stand on your day

Pages: `/finance/purchase/page/scans` and `/finance/purchase/page/sarvam?month=2026-09`, as the owner.

- **September in Marg: 81 purchase bills. 63 linked to a scan. 18 with no scan. 14 scans with no Marg bill.**
- **Scan work, 32 lines:** To scan 11 · Is this the bill? 8 · Choose the supplier 3 · Match the amount 4 · Waiting for Marg 2 · second scans 1.
- **F-691 — the list stood still.** These counts are what they were on 30-Sep. Nobody worked the list and nothing told anyone. Say from `audit_log` when the last tap on *Scan ka kaam* was, and by whom.
- **Of the 18 bills "with no scan", 6 probably have one** that was read differently and waits for a "Haan" (bills 75904, 78354, EP002243, IP006767, KEDAR 189, A.A. 416). One more (KEDAR 163) is in Marg twice. So about 11 have no paper on the server at all. Say whether any of the 11 sits in another lane of the asset app (scanned as a clinic bill by mistake): search every lane by bill-number tail and amount.
- **F-690 — the Sarvam page miscounts.** It says of the 63 linked bills: supplier wrong 13 · bill no. wrong 7 · date wrong 9 · total wrong 10 · items wrong 57. Read cell by cell:

| field | page says wrong | wrong in substance | what the rest are |
|---|---|---|---|
| supplier | 13 | 3 (scans 34, 72, 73: the shop's own name or a heading read as the supplier) | 10 differ by a full stop, a bracket or an ampersand's spacing ("PVT. LTD." / "PVT LTD", "(EXTN)" / "EXTN") |
| bill number | 7 | 4 (scans 63 and 92 read the drug-licence number; 45 and 99 misread digits) | 3 are the printed full number against Marg's short one ("YS/0585/" followed by the printed financial year, against "585") |
| date | 9 | 9 | 6 have only the year wrong, 2 the month, 1 is a day off |
| total | 10 | 10 | 4 large (the *Amount milao* four), 6 between Rs 6 and Rs 243 |
| item lines | 130 of 158 lines | not judged | batch 67 · name 36 · rate 33 · qty 22 · expiry 21 |

- All three of supplier, bill number and date are right on **47 of 63** in substance (35 by the page's count).
- **Scan 99** pairs a reading "15/0823/" plus the financial year with Marg's bill 672. Either a misread or a wrong link: look at the picture and say which.
- Only linked bills are in these figures. The 14 unlinked scans are the worst read, so the true rate over all scans is lower. Say that figure too.

## 3 · The build

### 3.1 The register — `purchase_app.py`; the page `/finance/purchase/page/scans`

The Scan links page becomes the month's bill register. Same address, `?month=YYYY-MM`, default the newest month that is not whole. No second page.

- **One row per Marg purchase bill of the month** (`purchase_bill.month`; Marg's bill date decides the month). Each row is in exactly one state:
  - **Verified** — its scan is linked and the four fields agree by §3.2.
  - **One thing differs** — linked, and one named field differs. The row names the field, both values, and whose line it is now (§3.4).
  - **No scan** — on the re-upload list, with the days it has waited.
  - **Entered twice in Marg** — as today, on Amir's list.
  - **Accepted without paper** — the owner's own tap, for a paper that is lost. Owner only, one tap, audited with the reason; it can be undone.
- **Under the bills, the scans that have no Marg bill**, each in one state: second scan (set aside) · near-match waiting for a "Haan" · supplier not read · waiting for Marg's entry (S452's list for Amir).
- **The head line, in the owner's English** (the shape; the figures are an example): "September 2026 — 81 bills in Marg · 63 verified · 6 one thing differs · 11 no scan · 1 entered twice · 14 scans with no bill." The month is **whole** when every Marg bill is verified or accepted without paper and no scan of that month is open. Then the line reads "81 of 81 ✓" and says when it became whole.
- The same one line on the owner's approvals page, Month section, through `sanjeevni_approvals`'s existing lines (no edit to the parent's page).
- Every figure on this page, on *Scan ka kaam*, on Amir's list and on the Sarvam page comes from **one function**. Two pages must not be able to disagree about a bill.
- Phone width: no sideways scroll. The sticky BACK bar and the up-arrow stay.

### 3.2 A bill is verified on what the scan reads well — `purchase_app.py`

One set of rules, used by the matcher, the register and the Sarvam counter alike.

- **Supplier:** equal after dropping punctuation, brackets, "&"/"AND", and legal-form words ("PVT", "LTD", "P", "M/S", a trailing town). Then the learnt spellings (`purchase_scan_alias`). The shop's own name, or a heading such as "WHOLE SALE CHEMIST & DRUGGIST", is never a supplier: treat it as "not read".
- **Bill number:** Marg's number, leading zeros dropped, equals **one whole run of digits** in the scan's reading. "YS/0585/" followed by the financial year has the run 585 and the year's own runs; Marg's 585 is one of them. A run that is the financial year, and any reading shaped like a drug-licence number (ending "/BLY" or the like), is never the bill number. Letters in Marg's number ("EP002243") are compared by their digit run, as S439 does.
- **Date:** the day and the month agree. A year other than Marg's is a misread and is ignored; the row may say "year misread", small and grey.
- **Total:** within Rs 1 is equal. Up to a setting `purchase.total_noise_rs` (default 10) is **verified, with the difference shown** and no task (the D622 rule: rounding noise is not a finding). More than that is *Amount milao*, as today.
- **Verified** = the total agrees, the bill number agrees, and at least one of supplier and date agrees. If the fourth differs it goes to §3.4 as one question; a year-only date difference and a punctuation difference never ask.
- **Learning:** each verified bill teaches the supplier's printed spelling (as today). If the scan's reading carries the supplier's GST number, a verified bill may teach "this number = this supplier", kept in the database only, never in a kit or a report (F-185); it is then the first test for that supplier. If the reading does not carry it, say so and skip this.
- Re-run the matcher on September with these rules **before anything else is built**, on a copy, and REPORT: how many of the 14 unlinked scans now link, how many of the 63 are verified without a tap, and every row whose state changes, by name. If a rule links a wrong pair on the copy, stop and report.

### 3.3 Item lines: judged by Marg's arithmetic and by learnt names, never by the scan's reading — `purchase_app.py`

- **Arithmetic.** For each Marg bill, the value of its own lines (`purchase_line`: quantity × rate, less the line discount, plus tax) against the bill's amount. **Measure this first on August and September and REPORT** how many bills agree within the noise setting, and what the usual differences are (round-off, a bill-level discount, a credit note). Then:
  - where Marg's lines add up to Marg's total **and** that total equals the paper's: the row carries a small tick "items add up". That is the item check;
  - where they do not: the row says by how much. No staff task from this in S454. The measurement decides the next step.
  - If the export does not carry enough to compute this for most bills, say so and build nothing more of it.
- **Learnt item names.** A new table (`purchase_item_alias`: supplier, the paper's item name as read, Marg's item) is taught only by a verified bill, and only where the pairing is certain: the bill has one line, or the quantity and the rate both agree and no other line of that bill shares them. The next compare looks the name up there first. A rename in Marg is followed through `item_alias` (D620).
- **The Sarvam trial line (D650) becomes two honest figures:** the four header fields by §3.2, and the item lines. In the item figure, "name" is judged through the learnt names. Batch and expiry are their own figure. Nothing in the item figure makes a task for anyone.
- **Batch and expiry are not verified from the scan.** They belong to the shelf: the arrival tap, the spot counts (S428), near-expiry (S343). Nothing is built for them here; say in the report what those three already catch.
- REPORT: Marg's line count against the scan's line count for September, so the owner sees how much of the item table the scan reads at all.

### 3.4 What is left reaches a person — `porders.py`, `porders.html`, `reports_tile.py`, `sanjeevni_approvals.py`

Staff pages in Roman Hindi; the owner's in English.

- **The re-upload list is *Scan karo*, as today,** on *Scan ka kaam*. Each line gains the days it has waited ("5 din se"), oldest first, and one more tap: **"Paper nahi mila"**. That tap sends the line to the owner as one Needs-you line ("Paper lost: KEDAR 160, 03-Sep, Rs …"), where his "accepted without paper" closes it.
- **A new group, "Paper par kya likha hai?"** — a linked bill where one field differs. The line shows the picture and two buttons: Marg's value and the scan's value (and "doosra" with one box, for the total and the date only).
  - Paper = Marg: verified; the misread is learnt.
  - Paper ≠ Marg: the line goes to Amir's *Marg sudhar* list through the path *Amount milao* already uses for "Marg galat"; it clears itself when an export shows Marg equal to the paper.
  - *Amount milao* stays as it is and is the total's form of this group.
- **Shavez's morning page** (`reports_tile`) gets one line while anything waits: "Bill scan baaki: 11 · sabse purana 12 din — kholiye", opening *Scan ka kaam*. It leaves when the list is empty.
- **The owner's Needs-you** (`sanjeevni_approvals`, the S444 mechanism) gets one line when the oldest line of *Scan ka kaam* is older than `purchase.scan_wait_days` (default 3), with the count and the oldest age; and one when a scan has waited for Marg's entry longer than `purchase.entry_wait_days` (default 3).
- **`DUTY_MAP`:** the duties "scan a bill Marg has and the server does not", "answer what the paper says", and "close the month's register" each get their row, their state and their door. The staff-eye walk asserts them.

## 4 · Pins

S452's TO pins, from `REPORT_S452.md`, each read live before the first edit. `porders.py` and `porders.html` were moved by the parent's S441 and by S444: read them whole from the box. `reports_tile.py` and `sanjeevni_approvals.py`: read live.

Not touched: `finance_app.py`, `portal.py`, `tile_grants.json`, `finance_approvals.html`, `asset_register.py`, `packs.py`, `supplier_msg.py`, `stock_app.py`, the crontab (the 23:59 re-match stays), the medical PC.

## 5 · Walk (scratch copies of `finance.db` and `assets.db`; rows keyed W454*; dates from today)

- **The rules, each on a crafted pair and on the September pair that showed it.**
  - "GUNINA PHARMACEUTICALS PVT. LTD." and "ESS KAY AGENCIES (EXTN)" agree with Marg's spelling. The shop's own name does not count as a supplier.
  - "YS/0585/" plus the financial year agrees with 585. A licence-shaped reading does not agree with anything. A financial-year run alone never links a bill.
  - A date with the year wrong agrees; with the month wrong it does not.
  - A total Rs 6 off is verified with the difference shown; Rs 243 off is *Amount milao*.
  - A wrong pair is not made: two bills of one supplier with the same amount and neighbouring numbers stay apart.
- **The register.** On the box's own data the head line's figures add up to the Marg bill count; every bill is in exactly one state; the scans below are each in one state; the same bill shows the same state on the register, on *Scan ka kaam*, on Amir's list and on the Sarvam page.
- **Whole.** A crafted month with every bill verified reads "N of N ✓". One bill accepted without paper keeps it whole and is named. Undoing it opens the month again.
- **Paper nahi mila.** The reception login taps it; the owner's Needs-you carries the line; his tap closes it; each step one audit row.
- **Paper par kya likha hai?** Paper = Marg verifies and teaches. Paper ≠ Marg lands on Amir's *Marg sudhar* and clears on a crafted export.
- **Items.** A crafted bill whose lines add up carries the tick; one that does not says by how much. A one-line verified bill teaches its name; a two-line bill with equal quantity and rate on both lines teaches nothing.
- **The Sarvam page.** Punctuation and prefixes are not counted wrong. September's header figures equal §2's "wrong in substance" column, or the difference is explained row by row.
- **Late work.** With a crafted *Scan karo* line 4 days old: Shavez's line shows, the owner's Needs-you shows; both leave when the scan arrives.
- **Staff-eye walk** (CLAUDE.md, "Every duty has a door") for the reception login, shavez, amir and the owner.
- **Earlier walks re-run:** S439, S440, S441's scan checks, S446, S452 — each adjustment named.
- **Negative control** on the box as it is.

## 6 · Done means

Kit `deploy_kits\S454_BILL_REGISTER\` · installed · published · `claude_code_briefs\REPORT_S454.md`, owner lines first:

- September's line as the register now reads it, and August's.
- How many bills became verified by the new rules without anyone touching them.
- The bills that still have no paper on the server, by supplier, bill number, date and amount — the list reception scans from.
- How many of Marg's bills add up to their own total, and what that says about the item check.
- What reception, Shavez and Amir will each see, in their own words.

Ending with:

```
https://followup.dr-manoj.in/finance/purchase/page/scans
```

```
https://followup.dr-manoj.in/finance/purchase/page/sarvam?month=2026-09
```
