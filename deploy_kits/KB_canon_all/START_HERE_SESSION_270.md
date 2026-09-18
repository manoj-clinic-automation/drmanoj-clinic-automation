# START HERE — SESSION 270 — written at the S268 close, 18-Sep-2026

**Project: Sanjeevni — Pharmacy & Marg.** Open in a fresh chat in that project. Run the project's own
`SANJEEVNI_START_HERE_PROMPT v1.1` Phase 0 first — **claim your session number on the board before
anything else (F-509)** — then come back here.

*Why 270 and not 269: the parent project's S267 close reserved Session 269 and wrote its own
`START_HERE_SESSION_269`. The board decides; if it has moved past 270, take the next free number and say
so in your first line.*

---

## §0 — THE NUMBERS, AND THE ONE RULE THAT MATTERS MOST AT YOUR CLOSE

**Canon at this close:** Archive **v1.107** · Fault **v2.95** · Register **v5.109** · Runbook **v190** ·
Sanjeevni Book **v1.4** · `live_pins_S268close.txt`.

**Next free: D550 · F-539 · A-D25 · kit S315 · Session 270.** The board wins if it is later.

*F-538 was minted at the S268 post-close: the owner's publish refused on a `__pycache__` sitting inside the
published `S313_SECTION_MAP` folder — F-512 broken by this session's own S314 rehearsal, caught by F-100's
guard. **Its rule is yours to keep: a rehearsal, walk or selftest never imports from `deploy_kits\`, and before
you hand the owner a publish, run `find <repo> -name __pycache__ -o -name "*.pyc"` and expect zero — the same
way the close already checks for `*.lock`.***

Consumed 18-Sep by **S268 (Sanjeevni)**: D544 · D548 · D549 · F-526 · F-527 · F-528 · F-535 · F-536 ·
F-537 · F-538 · kits S312 · S313 · S314.
By **S267 (parent)** in the same hours: D545 · D546 · D547 · F-529 … F-534 · kits S300 · S303 · S306 ·
S309 · S310.

**READ F-537 BEFORE YOU WRITE YOUR FIRST CANON FILE.** Twice now — S267 and S268 — a close has appended
to the canon versions it read at its **open**, while the other chat closed in between and took them.
S268's case was the worse one, and it is worth the thirty seconds it will cost you:

> Four canon files carry the session in their filename, so a collision there is a duplicated version
> number that a listing reveals. **Two do not — `Fault_Action_Register_v2_NN.md` and
> `START_HERE_SESSION_NNN.md`.** Writing those did not collide with the parent's. **It destroyed them**,
> silently, in a folder that publishes. They were recovered only because the owner's publish had carried
> them to GitHub twenty minutes earlier.

**So: list `KB_canon_all\` with `ls`, and read the board, in the minute before you write your first canon
file — not at your open.** If a file you are about to write already exists, read it back and prove it is
the parent you think it is. The recovery route, if you ever need it: **the published commit is the
backup** — clone in the cloud workspace (never `git` in the PC shell, F-511) and take the file back.

**YOU INHERIT NO CORRECTIONS.** S268 closed clean, with the fork repaired before any publish.

**THE OWNER'S STOCK-CHECK PART IS SETTLED AND IS NOT YOURS.** The 18 answers on step 2, *Try to match*,
are his and he will do them at his own time. **Do not ask, do not prompt, do not open with it, do not
treat it as a blocker.** Assume it will be done; he will tell you himself. Standing instruction, carried
forward verbatim, and it binds every session after this one too.

---

## §1 — YOUR WORK: THE MARG REPORT CONTRACT

This is the whole of your session unless the owner redirects you. His words on 18-Sep, and the reason:

> *"Now I want you to define all the reports and the frequency at which you require them from the Marg
> ERP software and then test them individually against your parser for any defects. The category wise
> orthotic list and the salt wise list and the purchase bill wise the sale item wise the purchase item
> wise and any other report from Marg which carries the item name — there should be no confusion in our
> system as to what the item name is, what the category is, what the MRP is, and if the prescribed
> discount is also mentioned in any Marg output list such as the category list or salt wise list, that
> should also be captured."*

> *"I want you to work from the very thing that this system is built from. That is the various type of
> Marg exports you read. And then you populate the data here. Because my confidence in your work is
> shaken right now."*

**It is shaken for cause.** S268 minted **F-535** and **F-536** and found a third instance of the same
error: three beliefs in this estate were taken from the *surface* of a report and never checked against
a store. One of them — the salt importer reading Marg's page header `SANJEEVNI MEDICOS` as a salt — had
**put an invented pair in front of him on the very step-2 screen he is being asked to answer.** Read
Runbook v190 §3 before you write a line of code.

### 1.1 — What is already measured. Do not re-derive it; verify it and move on.

*All figures below were read from the box or the PC at S268 and are stated so you can check them, not
so you can trust them.*

**The router's signature registry — `D:\Downloads\margsync\MargPull\signatures.json` — holds 18
signatures across 15 archive families.** Matching rule: **title_regex AND header must both match**, else
the file is refused. A partial match is never parsed; unknown files are quarantined, never guessed at.
**Adding a report type is a DATA EDIT here — no code change** (`marg_router.py --learn <file>` prints a
ready-to-paste block).

**Finding 1 — the category list has no signature, and the owner's own export is sitting refused.**
His `MARG ORTHOTICS CATEEGORY LIST 1 DEPT 2026.XLS`, exported 18-Sep at 07:48, is in
`MargArchive\_REFUSED\` with the verdict:

```
reason: no signature matches this title: 'CATEGORY WISE ITEM LIST' | no data dates could be established
header: ['S.No. DESCRIPTION', 'PACKING', 'P.RATE', 'S.RATE', 'M.R.P.']
```

The router was **right** to refuse it. Its header is identical to `SALT_WISE_ITEM_LIST`'s; only the
title differs — which is exactly why title-and-header are both required. **This is your first, cheapest
win: a signature for `CATEGORY_WISE_ITEM_LIST`, and the two refused copies re-driven through the router
so they file themselves.** Note the second refusal condition too: *no data dates could be established* —
an item list carries no date range, so it needs `dating: filetime`, the way `STOCK_EXPIRY` does.

**Finding 2 — and this is the structural cause of F-535 and F-536.** Of the 18 signatures, **exactly
ONE carries `deep_verify: marg_report`** — the full arithmetic-and-truncation check. It is
`SALE_BILLWISE / DETAIL`. **All seventeen others get `structural` only**: title/header/date agreement
and a clean end. So the estate has had a real verifier all along and has been pointing it at one report
out of eighteen. Every belief this session had to retract came from one of the seventeen.

**Finding 3 — the clip widths, re-measured across April–September (F-535).** Sale export **20**
characters · purchase export **27** · **Marg's own item master 29.** S236's *"truncation is gone"* was
true of the printed bill and false of the export we import, and its own instruction to re-measure went
unread for nine sessions. 29 is a hard ceiling on any rename — it had already broken two of S268's 22
rename proposals before they were caught.

**Finding 4 — the archive's coverage, counted at this close.** `MargArchive\`:

| family | files | newest | what it is worth to you |
|---|---|---|---|
| `SALE_BILLWISE` | 38 | 2026-09 | the only deeply-verified report on the estate |
| `SALE_DAILY_PRINT` | 1 | 2026-09 | text variant |
| `SALE_BOOK` | 1 | 2026-06 | **stale** |
| `SALE_RETURN` | 3 | 2026-04 | **stale — and F-527 says no purchase return is stored at all** |
| `PURCHASE_BILLWISE` | 18 | 2026-09 | |
| `PURCHASE_ITEMWISE` | 14 | 2026-09 | carries the item name |
| `PURCHASE_BILLITEMWISE` | 5 | 2026-09 | the richest purchase report |
| `PURCHASE_SUPPLIERWISE` | 6 | 2026-09 | |
| `SALT_WISE_ITEM_LIST` | 6 | 2026-09 | where F-536 lived |
| `ITEM_MASTER` | 3 | **2026-08** | **stale, and it is the name authority** |
| `STOCK_CLOSING` | 32 | 2026-09 | |
| `STOCK_VALUATION` | 2 | 2026-09 | |
| `STOCK_EXPIRY` | 9 | 2026-08 | |
| `STOCK_ITEM_LEDGER` | 4 | 2026-04 | **stale** |
| `CATEGORY_WISE_ITEM_LIST` | **0** | — | **no family, no signature — Finding 1** |
| `_REFUSED` | 26 | 2026-09-18 | the two category copies are the newest two |

### 1.2 — The reader that already exists. Use it; do not start again.

**`D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S268\reader\margparse.py`** — 153 lines. It is **NOT
installed anywhere**, and `READ_ME.txt` beside it says so. Installing it is part of this work, not a
prerequisite to it.

What makes it different from what it replaces:

- It classifies **every** row **positively** — `ADVERT, CONTINUED, PAGENO, SHOPNAME, TITLE, COLHDR,
  STRAY, ITEM, HEADING, ANOMALY`, in that order. **Nothing is identified by exclusion.** F-536 was an
  exclusion rule.
- It carries **an independent witness that Marg gives free: every item row is numbered, and the
  numbering restarts at 1 under every group heading.** `parse()` asserts it — on a HEADING it sets
  `want = 1`; on an ITEM it requires `r.n == want`. **A misread heading is therefore contradicted by the
  very next row**, loudly, instead of silently becoming a salt.
- It was run over six exports and **made to fail on purpose at exactly the two rows where the old bug
  lived**, which is the standing rule the Fault Register now carries:

> **A report is a surface. Before any figure from it enters canon, the reader that produced it must be
> able to fail — and must have been made to fail on purpose at least once.**

### 1.3 — What the session must produce

**Test every report type individually.** That is the owner's instruction and it is the shape of the
work: one report type at a time, its own sample, its own assertions, its own verdict — not one sweep
that reports a percentage.

For each report family that **carries an item name** — at minimum `ITEM_MASTER`, `SALT_WISE_ITEM_LIST`,
`CATEGORY_WISE_ITEM_LIST` (once it has a signature), `PURCHASE_ITEMWISE`, `PURCHASE_BILLITEMWISE`,
`SALE_BILLWISE`, `SALE_DAILY_PRINT`, `STOCK_CLOSING`, `STOCK_VALUATION`, `STOCK_EXPIRY`,
`STOCK_ITEM_LEDGER` — establish and write down:

1. **The grammar** — every row class that occurs in it, named positively, with a real sample line.
2. **The witness** — what in *that* report independently proves the reader right (the serial restart, a
   stated total, a row count, a bill total that must re-add). **A report with no witness is a report
   whose figures do not enter canon.** Say so plainly rather than inventing one.
3. **The fields it authoritatively carries** — of `item name · category · salt · MRP · packing ·
   p.rate · s.rate · prescribed discount`. He asked specifically: **if a discount is printed in the
   category list or the salt-wise list, capture it.** Check; do not assume either way.
4. **The clip width** — measured in that report, in the current month, not inherited.
5. **The frequency** he should export it, and **why**, in one line he can act on. This is the
   deliverable he named first. Give him a short list he can put beside the Marg screen, not a table of
   eighteen rows.
6. **The deliberate failure** — the row you corrupted on purpose and the assertion that caught it.
   Rule 1.2. **No verdict without it.**

**Then the contract itself**, written to canon: **one document that says, for every Marg report this
estate reads, what it is, what it proves, what it may be trusted for, and what it may not.** That is the
thing he is asking for when he says *"there should be no confusion in our system as to what the item
name is, what the category is, what the MRP is."* Name it `MARG_REPORT_CONTRACT_v1.md`, put it in
`KB_canon_all\`, give it a manifest row, and supersede `MARG_REPORT_EXPECTATIONS.md` explicitly where
they overlap.

**And then, and only then, populate.** His last sentence is the order of work: *work from the exports,
then populate the data here.* Do not re-populate `purchase_salt_marg` or anything else from a reader
that has not yet been made to fail.

### 1.4 — The rails on this work

- **D549 binds you: the 22 renames wait until count #1 closes.** `stock_count_item`, `stock_diff`,
  `stock_diff_lane`, `stock_voucher_line` and `stock_match` all hold the item **by the raw name it had
  on 6 September**, and **nothing follows a rename**. Your work here must not touch an item name.
- **Nothing you do may disturb the 06-Sep physical stock check.** His standing instruction. Re-reading
  and re-parsing exports does not touch it; **rewriting a table the count reads does.** If a correction
  you find needs a stored table changed, say so and stop — that is a kit and a decision, not a fix.
  **F-526 is already parked on exactly this rule** and is yours to repair when the count closes: step 7
  windows on `stock_voucher_entered.entered_at`, the moment Amir told the server, instead of on the
  voucher's own date.
- **The 22 renames and the salt corrections are already written up** and need no rework:
  `S268_ORTHOTIC_CORRECTIONS_FINAL.md` (v3 — the `SANJEEVNI MEDICOS` claim is retracted in it in full),
  `S268_ORTHOTIC_NAME_FIX_THE_22.md` (v2 — both 30-character targets fixed; longest new name exactly
  29), `S268_MARG_DATA_SETTLED.md`. All three are in this project's knowledge and in
  `03_WORKING_PAPERS\S268\`.
- **F-512:** build in scratch, `py_compile` (`python`, not `python3`), copy into `deploy_kits\` only when
  final. **F-511:** no git in `device_bash` against a connected folder. **F-510:** read the clock, never
  estimate it.
- **Chat short. Give him the publish double-click and the one VPS line — nothing else** unless he asks.

---

## §2 — THE ONE THING WAITING FOR HIS DOUBLE-CLICK

`S314_SECTION_SCOPE` is **built, publish-ready and NOT installed**. It is rungs 2 and 3 of the count-#2
plan: `stock_count.section`, and `_pad_family()` measuring what is owed against the round's **scope**
instead of the whole shop. Pin: `/root/finance/stock_app.py` `10be8a9e` → `1b473fbf`. It requires S313
live, which it is. Its walk holds the 06-Sep round against the live module and **every figure, and the
entire hub payload, must come back identical** before it will install.

**Do not push it.** It is his to run when he wants the sectioned count. If he asks, the line is — and note the
installer's FULL name, because the S268 close first handed him `install.sh` and the shell answered *No such file
or directory*; **every installer in this estate is `install_<KIT>.sh`, and a line handed to the owner is read off
the kit folder, never typed from memory:**

```
cd /root/deploy/repo && git pull && bash deploy_kits/S314_SECTION_SCOPE/install_S314_SECTION_SCOPE.sh
```

---

## §3 — WHAT NO STORE HOLDS (A12b, carried into your open)

- **No purchase return is stored anywhere on this box (F-527).** The claim queue's self-closing half is
  written and asleep behind a live capability test until one is. If your report work turns up a
  purchase-return export that Marg can produce, **that is the unlock** — say so; it is worth a kit.
- **`margparse.py` is installed nowhere.** It exists only as a working paper.
- **The category list has no archive family.** Finding 1.
- **`stock_item_section` is read by nothing yet**, by design (D548). It decides scope only.

---

*START_HERE_SESSION_270 · written at the S268 close, 18-Sep-2026 · Sanjeevni project · canon at this
close: Archive v1.107 · Fault v2.95 · Register v5.109 · Runbook v190 · Book v1.4.*
