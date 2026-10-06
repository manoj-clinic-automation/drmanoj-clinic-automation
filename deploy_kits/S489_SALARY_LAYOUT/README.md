# S489_SALARY_LAYOUT

**One line on the VPS (after the publish):**

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S489_SALARY_LAYOUT/install_S489_SALARY_LAYOUT.sh
```

`DRY=1` in front of `bash` runs every gate, the walk on the box and the ledger's dry run, and writes nothing.

## Why — the owner, 06-Oct-2026

Looking at Sheet 2 of September after the ledger close: *"where there is an instalment being populated. This is
lacking clarity for me and for staff both."* One of Surendra's advances, paid back in equal monthly parts, was on the
page as three separate advances, one under "Recovered in one go", one under "On instalments", its instalment never
stated, and the month's total mixed the instalment with two ordinary advances. Three mock-ups later his rulings were:

**D681** — advances are shown in **two tables that never mix**: *this month's advances* (cut in full from this
salary) and *instalment loans*, **one line per person per loan** however many parts it was handed over in
(instalment, paid n of N, cut this month, balance, end month, a month strip), with **one closing line per person**
(advances + instalment = cut this month). No interest-loan row on the shared sheet. A **salary slip only for a person
with a running instalment loan**, in one format.

**D682** — **Darpan goes back on the common salary sheet at his salary less the long-term loan's standing
instalment**; late, absence, overtime and incentive are worked on the full salary; his ordinary advances sit on the
common sheet like everyone's. **The long-term instalment lives only on his private page**, which becomes **one
loan-ledger table** for the loan with interest from April 2026 (opening balance as at 31-Mar-2026, the loan
workbook's agreed position). A month he asks to skip shows only there: the common sheet does not change and the
instalment kept aside is paid to him on the private page. From September 2026 (he unlocks and re-locks). And
**April 2026's flat Rs 1,000 comes off the loan** ("Come off").

No person's salary, balance or instalment is written anywhere in this kit (F-31).

## What changes

| what | how |
|---|---|
| `/root/staff_register/salary_policy.py` | v1.16 `92aecbe3` → v1.17 (md5 in `SUMS.md5` and the installer's `TO=`), full file. `make_s489.py` rebuilds it from the live bytes by exact anchors, each found once, with four blocks in `blocks/`. |
| Sheet 2 | tables **1 · This month's advances**, **2 · Instalment loans**, **3 · What each salary bears this month**. The holds, fines and part-time sections are untouched. Nobody is sent to a separate money page. |
| Sheets 3 and 4 | Darpan is a row like everyone (salary less the instalment, Advance without the long-term instalment). The SHEET 5 own sheet is retired. A slip follows Sheet 4 for each person with a running instalment loan. |
| `…/sheet2?ym=…&staff=Darpan` | the private **loan ledger**: opening balance, one row per salary month (April–June 2026 from `loan_pages.json`, later months from the ledger's own rows), totals, the next month, a signature line. |
| `/root/staff_register/loan_pages.json` (new) | written by `data_s489.py`: Surendra's three-part advance is one loan; which of Darpan's loan months before the ledger began were skipped and which paid. **No balance, no instalment, no salary** — the engine works the opening balance back from the ledger's own figures, so the page cannot disagree with the ledger. |
| the staff ledger | ONE row by `restate_s489.py`: `LOAN_CAPITALISE` −1000 on loan `b1eb7a8e419e`, dated 2026-04, stamped like the April skip row (2026-07), tag `restate=S489`. `staff_ledger.py` is not edited — its balance arithmetic (amount + capitalised − recovered) already carries it everywhere. |
| the forward plan (the month strip, "next month's instalment") | follows a **defer or a skip already recorded** in the ledger, exactly as the close will. (The live engine's plan did not; a deferred schedule read one month short.) Holds, and defers not yet recorded, are still not foreseen. |

**No rupee moves except that one ruled Rs 1,000.** Every figure is still the staff ledger's own (D349/D442). The
engine's own arithmetic — day rate, minute rate, leave, late, overtime, incentive — runs on the full salary and is
not touched; for a private-loan person only the *shown* salary, advance and net change, and one identity always holds:

> full net = common-sheet net + what the private page pays him (nothing in an ordinary month; the instalment in a month it was not taken)

`staff_register.py` is not edited: the lock desk, the lock, the frozen-sheet reader and the totals read the same
fields as before. In a skipped month the lock's TOTAL PAYOUT is the common sheets' total; the instalment paid to him
is on his private page only — as ruled.

## Proof

- `salary_policy.py --selftest` — the old checks plus the new pure functions on made-up people: one loan in three
  parts, same-month advances, a private loan with its interest-free part, a skipped month, a defer on the loan
  alone, a month before the close, the loan ledger with a stated opening, with an opening worked back, and with no
  history record; a record whose ledger adjustment is not the one it names; a recorded defer and a recorded skip
  moving the plan; a one-salary advance getting no slip; a broken `loan_pages.json` (never raises).
- **`walk_s489.py` — on the box, before anything is written** (and offline on a box-shaped tree built from the
  06-Oct 01:35 bundle's own code and a live-shape ledger: the box's own `close_month('2026-09')` run over it writes
  exactly the rows the live close wrote). The LIVE engine and the kit's compute the same months side by side.
  Every figure of every person is identical except Darpan's shown figures, and **what those must be is worked out
  in the walk from the ledger's own lines**, not taken from the kit engine. Table 1 + table 2 = the Advance figure
  = the ledger's 'deducted' as the live engine reads it; every open ledger line in exactly one table; a loan handed
  over in parts is one line; **the figures printed** on Sheet 2's closing table, on each slip and on the private
  page are read back out of the HTML and compared; the common pages never show the private loan; the frozen Sheet 3
  reads back through `staff_register.locked_snapshot()` and adds up. Then the restatement on a scratch copy of the
  ledger — exactly Rs 1,000, nothing else moves, no new closed month — and the private page **row by row against
  the ledger's raw rows**. Offline counts: see the build brief. **29 negative controls, each red on its own check.**
  Also walked green on trees with a deferred schedule, a deferred group, a deferred loan, a closed skipped month,
  a new advance, and a second person with an interest loan.
- September 2026 on the real figures (offline, never in git): the kit engine's ledger side equals every person's
  live Advance figure; with the live Sheet 3 / Sheet 5 figures laid over it every net re-derives to the live net and
  the lock total is unchanged. The pages were rendered to PDF and read by sub-agents; that PDF is what the owner was
  shown before the install.
- `after_s489.py` — after the restart, on the engine as placed, with the same worked-out-here checks; red puts the
  old engine back.
- The installer rehearsed in a sandbox: dry, green, pasted again, lock held, a moved pin, a corrupt kit, red after
  placing (health), red at the after-check, the engine in but the ledger row missing, a slow start, and a red
  after-check on a second paste (the old engine goes back from its backup).
- An independent review (a second reader, with the code and no brief from the builder beyond the rulings) found one
  blocking fault and a dozen smaller ones in the first build; every one is closed in this one and the list is in
  the session's evidence folder.

## After the install — the owner

1. Read Sheet 2 of September: `https://followup.dr-manoj.in/register/salary/flow/sheet2?ym=2026-09`
2. Unlock September on the lock desk (a reason is asked) and lock it again:
   `https://followup.dr-manoj.in/register/salary?ym=2026-09` — the lock saves the sheets as they then look.

## Known, said

- The full salary is not hidden from someone who divides: his one-day leave cut is worked on the full salary.
- If the staff ledger cannot be read at all, the sheet says so in red and every Advance is empty; in that state his
  row shows the full salary, because the instalment is the ledger's to say. Nothing is locked or printed then.
- **A month's skip is NOT yet one button.** The ledger today offers two, and neither is the ruled outcome by
  itself: **Skip** pauses everything and pays the instalment to him, but adds the flat Rs 1,000 to the loan each
  time; **Defer** adds nothing the first two times a year, but must be pressed on BOTH of his long-term lines —
  pressed on the loan with interest alone, the ledger simply takes the same instalment for the interest-free part
  (the private page then says so: "Not on this loan"). To be put to the owner before the first skip is asked for.
- From now on an advance paid back over several months should be entered ONCE with its schedule; then it needs no
  group record in `loan_pages.json`.
- A slip printed BEFORE the ledger close says on its face that it is not final (the advances are not cut yet).
- The engine's Sheet 3 footnote says "D+I fine: Rs.15/day each" while September's figures charge the dress days
  only — as the live engine already printed; not changed here, to be read at the next session.
