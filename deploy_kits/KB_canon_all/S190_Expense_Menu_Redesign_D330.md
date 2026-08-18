# The Expense Menu, redesigned — a derived ceiling, evidence on every spend (D330 candidate · S190)

**Design settled at S190 on the owner's rulings. Status: READY FOR SIGNATURE — every §8
item is ruled or verified; nothing in this document rests on an unopened file.**
**Supersedes D329 (the Advance Pool) — §6. The staff-wide advance policy is a SEPARATE
contract — §7.**

---

## 1 · The rulings

1. **Three categories**, replacing the five shipped at S189:
   **salary advance · home expenses · other expenses.**
2. **Salary advance** shows the **total already taken this calendar month** inline, beside
   the **maximum permissible**, *before* he types.
3. **The ceiling is derived, never typed:** a **per-staff percentage of base salary,
   rounded down to the last ₹100.** Default **50%**. Darpan's exception **75%** —
   75% × ₹20,000 = **₹15,000**.
4. **Over the ceiling, nothing may be drawn from this system.** It becomes a **special
   advance** through the regular staff pipeline.
5. **Home expenses** covers personal spending from the drawer, including **courier / COD
   deliveries for personal items** — which is why courier is *not* a business head.
6. **Home expenses and other expenses are free text with COMPULSORY evidence — no escape
   hatch.** The working pattern is stated by the owner: Darpan **photographs the bill when
   he pays**, and **uploads the saved picture when he files the expense the next day**. So
   the upload path is not a convenience beside the camera — it is the primary path.
7. **Live capture and file upload must both be available.**
8. **Petty expenses stay OUT of this system.** Small spends (tea, cleaning, courier
   handling and the like) run on a separate **manual physical book**. A digital petty
   expense book for a few staff members is **PARKED** for later — a Register parked-items
   entry, not a build. This is what keeps the compulsory rule livable: nothing small
   enough to lack a bill ever reaches this menu.

## 2 · What already exists, read before designing (F-137's rule)

Surveyed against the live bytes (`finance_app.py` `5cb73ff8…`, `finance_entry.html`
`1c7d2dc3…`, recovered **by hash**, D188 — not from the repo, whose `finance/` tree is
eight builds stale).

- **The menu** is one authored tuple, `EXPENSE_MENU`, with `EXPENSE_LABELS` derived. The
  save already refuses a skipped category and refuses `other` without details.
- **The scanner is already generic.** `/finance/scan/<date>/<doc_type>` builds a
  `window.SCANNER_CONFIG` — `uploadUrl`, `uploadFields`, `nameBase`, `title`, `backUrl`,
  `allowIdCard`, `allowBatch` — and hands to a shared widget at
  `/root/assetapp/scanner_widget.js`. **Per-expense evidence needs no new scanner.**
- **Attachments survive a re-save**, because `attachment` keys on `day_entry_id` and the
  `day_entry` row is kept. Expense rows are not so lucky — §3.
- **No ceiling machinery exists.** `month_to_date` in the code is *revenue*.
- **`cash_adjustment` is not a general-purpose back-entry.** It is wired to the physical
  cash-count reconciliation. It must not be used to post an advance.

## 3 · The blocker: expense rows have no durable identity

**`day_expense.id` does not survive a save.** Every re-save runs
`DELETE FROM day_line, day_expense, cash_movement, day_noncash_bill WHERE day_entry_id=?`
and re-inserts from the payload. Rows are destroyed and recreated with new ids. The page
compounds it: `loadDay` fills back **only** total, UPI and scan ticks.

So evidence attached to an expense row would be **orphaned by the next save of that day** —
file still on disk, nothing pointing at it, no error raised. With evidence now
**compulsory**, that is worse than untidy: the day could fail its own File check for a bill
that was in fact attached, or pass while pointing at nothing.

**The re-save fix is therefore a prerequisite, not a parallel backlog item.**

## 4 · Where the evidence check lives

**Evidence is enforced at FILE (submit), never at Save** — because a scan cannot attach
until the day exists (`409 no_day`: *"Save the day first, then attach its scans"*).
Requiring it at save would make the expense unsaveable.

This is the house pattern already, not an invention: the day's `REQUIRED_DOCS` are checked
`if submitting and missing_docs`, with a typed `missing_scan_reason` escape hatch. Expense
evidence follows the *timing* of that pattern but **not the hatch: the owner has ruled it
absolute.** A home or other expense with no evidence attached cannot be Filed, full stop.
The workflow that makes this livable is the owner's own: photograph at payment, upload at
filing. And petty spends — the case where a bill genuinely may not exist — never enter this
system at all (§1.8).

## 5 · The build, in order

| kit | contents |
|---|---|
| **`S190_E2a`** | `loadDay` refills expenses, movements and non-cash bills · the save becomes a true **edit** · every expense row carries a **stable key** surviving re-save. Closes the named draft-resave hazard and creates the identity §3 needs. |
| **`S190_E2b`** | the three-category `EXPENSE_MENU` · the per-staff **percentage-of-base** ceiling with month-to-date shown inline · **hard refusal** server-side, the figures in the message (F-140: a check that can fail says why) |
| **`S190_E2c`** | per-expense evidence: upload endpoint · `attachment` extended with the expense key · scan route reusing the existing widget with a per-row `uploadUrl` · live capture **and** file upload · **the compulsory-evidence check at File** |

E2c ships the mechanism and the requirement **together** — a rule with no way to satisfy it
is not shippable.

Each kit rehearsed offline against a store carrying the **live store's shape** (F-140),
projection written before measuring, and any count-equal kit proving itself by
**reproducing** the failure it cures (F-138).

### The ceiling, precisely

- `advance_pct` is a **per-staff setting** (default 50, Darpan 75). The ceiling is
  `floor(base × pct ÷ 100 ÷ 100) × 100`. **Nothing stores the number ₹15,000** — F-136:
  duplicate a value and you have created a second thing to keep true.
- Scope: **calendar month**, per unit, `category_fixed='salary_advance'`, summed across the
  month's draft *and* approved days.
- Refusal message carries both figures: *"Advance this month ₹15,000 of ₹15,000. This one
  cannot be drawn here."*
- **Base salary, not gross.** The outstation ₹250/night is in salary but unknown until
  month-end; the ceiling must be displayable before he draws. Stated, not assumed.
- Note the two scopes deliberately coexist: this ceiling is **calendar-month**; the loan
  skip counters are **Indian FY** (D250).

## 6 · What it does to D329

D329's pool, the B6 push-on-approval bridge, the scoped token, idempotency by expense id
and the one-tap LINK card **all existed because advances arrived random and unbounded.** A
derived hard ceiling removes that premise: at most twelve deliberate rows a year, which
wants typing, not plumbing.

**D329 is superseded, not amended** (D202 — no canonical document is a delta). Nothing of it
was built, so nothing is stranded. `S190_SL1`, the token step and `S190_F1` fall away.

Kept from it: the Apr–Jun **₹40,000 stays out** (verified recovered), and advances remain
**per-staff by construction**.

## 7 · What is NOT in this contract

The **staff-wide advance policy** — inline month-to-date for every staff member, the 50%
default, special advances, instalment repayment, and the **uploaded written application** —
is a change to **`staff_ledger.py`**, a separate live system serving all staff. It gets its
own contract and its own kits. Folding it in here would produce one document making claims
about two systems, which is the shape this project keeps finding faults in.

Also untouched: the D250 loan engine. The clinic unit IS in scope for the expense
categories and evidence — see §9 — but never for a salary-advance path.

## 8 · Open before signature

1. ~~Shop expense~~ **RULED:** petty spends run on the separate manual book (§1.8); a
   digital petty expense book is **parked**, not built. Anything large enough to reach this
   menu has a bill.
2. ~~The widget's file-upload path~~ **VERIFIED ON THE BOX (owner-run grep, S190).**
   Line 51 of `/root/assetapp/scanner_widget.js`:
   `<input type=file id=cam accept="image/*" multiple>` — a file input with **no
   `capture` attribute**, so a phone offers BOTH camera and gallery; the
   photograph-at-payment / upload-at-filing flow works natively. Line 182 enumerates
   `videoinput` devices — a live-capture path exists beside it. Both owner requirements
   are already in the shared widget; E2c reuses it unchanged.
3. ~~Home expenses in reporting~~ **RULED: yes.** Home expenses are totalled **separately
   in the books as the proprietor's drawings**, not mixed into business expenses. E2b's
   reporting surfaces (day totals, month grid, tile) carry the split.
4. ~~Clinic unit~~ **RULED: in scope, EXPENSES ONLY — see §10.** The clinic entry gets the
   **home expenses / other expenses** categories with the same compulsory evidence.
   **NO salary-advance path at clinic** — which is not a removal: the clinic path has
   never had one (*"clinic expenses are plain drawer expenses (no salary-advance path)"* —
   live code, surveyed today). Staff advances stay in the Staff Ledger pipeline, all units.
5. ~~The escape hatch~~ **RULED: absolute.** No reason-instead-of-scan for expense
   evidence. §4 records it.

## 9 · The clinic unit (ruled in at signature — expenses only)

The clinic entry path (`/finance/clinic/entry`, makers shavez/alisha/shivani) today takes
free-text expenses with a required note (`expense_note_required`, min 3 chars) and nothing
else. Under this contract it gains:

- the **two-category menu**: *Home expenses* · *Other expenses* — no salary-advance
  option, deliberately (§8.4). The owner's rule holds across units: **no staff advance is
  ever drawn from a drawer**; advances live in the Staff Ledger pipeline.
- the **same compulsory evidence at File**, same photograph-at-payment / upload-at-filing
  flow, same absence of any escape hatch.
- the **same drawings split in reporting** (§8.3): clinic home expenses total into the
  proprietor's drawings, not business expenses.

Build impact: the clinic surfaces ride the SAME three kits — E2a's re-save fix must cover
the clinic save path too (it has the same delete-and-reinsert shape), E2b adds the clinic
menu, E2c the clinic evidence check. No fourth kit; one more rehearsal store shape per kit
(the clinic store differs from medical — F-140 applies per unit).

## 10 · Parked at this design (for the Register's parked-items section)

- **Digital petty expense book** for a few staff members — replaces the manual physical
  book *some day, on the owner's word, not before*. Listed so it is not forgotten; not a
  backlog item, not a build, and nothing in this contract depends on it. (The D17/ClickUp
  parking pattern.)

---

*Design S190 · becomes D330 on the owner's OK · supersedes D329 · builds as
S190_E2a → E2b → E2c. Next free after: D331 · F-141.*
