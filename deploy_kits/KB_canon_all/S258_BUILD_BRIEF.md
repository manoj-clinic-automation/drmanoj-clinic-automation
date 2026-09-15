# S258 BUILD BRIEF — 15-Sep-2026

*The one document written for you this session. Everything else is evidence and is on the shelf.*

---

## IN ONE PARAGRAPH

The maintenance work that kept being *owed* at closes now runs itself every night, and the close's
job changed from doing it to checking it. Along the way the server's own code came within reach for
the first time, which let your Register be proved against the live machine in bulk — **109 pins, 109
matched** — and which exposed **six live files that had no backup anywhere.** Those are now carried.
The Sanjeevni Book was checked against the running system and brought up to date. Two of my own
findings turned out to be wrong and were retracted in public, and both became rules so the same
mistake is harder to make again.

---

## WHAT IS DIFFERENT ON YOUR MACHINES

**Nothing you have to remember.** That is the point.

| | before | now |
|---|---|---|
| the Cowork manifest | rebuilt when a session remembered | 03:10 nightly |
| the SSD mirror | **owed since 8-Sep** | 03:10 nightly, every CRC tested |
| the folder counts | eyeballed off a listing | measured, with what grew named |
| the VPS code bundle | in a Drive folder no session could see | copied where a session can read it |
| the canon gate | silently stopped covering two files | checked and repaired nightly |
| a missed 03:10 | **silently skipped** | catches up next time the PC is awake |

**One line shows and changes every job on the server:**

```
bash /root/finance/sanjeevni_switch.sh status
```

**And one file is the only thing you ever need to open about papers:**

```
D:\Downloads\_kbtools\PAPERS.bat
```

---

## THE FIVE KITS

**S272** put three maintenance steps into the 03:10 nightly. **S273** widened the nightly code bundle
so six files that existed in no backup are carried. **S274** gave the four Sanjeevni server jobs an
off switch — the same one your two PCs got at S259. **S275** gave the canon gate an owner. **S276**
made the nightly able to catch up when the PC was off.

Every one was proven before it ran on anything real, and two of them were proven against **a mock
server built out of your box's own nightly bundle** — the real tree, the real filenames, the real
bytes.

---

## THE FOUR THINGS WORTH KNOWING

### 1 · Six files would not have come back

Holding the code bundle against your pin list — a comparison nobody had been able to make before
this session — found **six files marked LIVE with no byte-exact copy in any store**: not the bundle,
not GitHub, not the encrypted backup, not the SSD. Among them **the live item spine**, **the asset
register application** behind `assets.dr-manoj.in`, and **the file that decides what your health page
watches**.

No single backup was misconfigured. Each excludes those files for a reason that is correct on its
own. **The gap lived between them.** S273 closes it, and the routine now says to run that comparison
whenever a new live file is pinned.

### 2 · Two surfaces disagree about your stock, and it matters

Your hub says **9 items differ**; the table behind it says **6**, for the same night's data. Neither
is obviously wrong.

The six are named, and each difference is **exactly one whole purchase** — the item's most recent
one, all dated 10–12 September, all from a single export your server already has. So nothing is lost
and no money is affected. But the shadow's agreement is the stated condition for retiring the jobs on
your PC, and **until the page and the table agree, that cannot start.** One command on the server
settles it; it is the first item for the next session.

### 3 · I was wrong twice, and said so

**`staff_master.csv`** was reported as having no backup. It does — I read one of two lists in the
backup script and stopped. **`AGARWAL SURGICALS AND MEDICALS`** was reported as having the word
CHEQUE inside its name in Marg. It does not — that is a lane badge on the page, and reading the page
as text ran the two together.

Both reached the Book before I caught them. Both are corrected there with the retraction written in
rather than deleted, and both are now rules in the routine: *a page read as text is not the data*,
and *a store is not checked until every one of its lists is read.*

### 4 · One number on your paper shelf is broken, and I caught it because it looked too good

The shelf says **0 papers never cited**. Yesterday it said 193. **Nothing about the papers changed.**
The shelf checks whether a paper's name appears anywhere — and the list it checks against is now the
nightly inventory of *every file on the machine*, so of course it finds every paper. The number
cannot be anything but zero from now on.

It is worth telling you not because it matters much, but because of the shape: **a fault that
reports itself as success.** No error, no red, a dashboard showing a problem apparently solved
overnight. The only reason it was checked is the standing rule that **a result that would be pleasant
if true gets checked harder.** I have written it up as F-491 and I fix it next session; until then
that one figure on `PAPERS.bat` is not to be read. Everything else on that page is sound.

---

## WHAT IS WAITING ON YOU — unchanged by this session

The head of your list has not moved: **the first cheque** (September owes ₹400 to AGARWAL SURGICALS
and the register is empty), **two vendors' bank details**, **KEDAR PHARMA's ₹310 in July**, and
**August — Check it now, then Lock it.**

```
https://followup.dr-manoj.in/finance/purchase/page/cheques
```

```
https://followup.dr-manoj.in/finance/purchase/page/pay/2026-08
```

*(One small correction to that list: AGARWAL SURGICALS **is** in your vendor register, with a phone.
What it is missing is only the bank account — account name, number, IFSC, branch. Give those and it
moves off the cheque lane by itself.)*

---

## WHAT I CHANGED ABOUT HOW I WORK

You said: *"don't leave it up to my discretion. And make it a part of your routine whenever you deem
it to be run. Or either run it yourself."*

You were right, and about that specific case entirely — **the install had already happened**, and the
step I handed you was one I had invented. It is now standing rule 11, and the close-out routine and
the start-up prompt were both rewritten (**v14** and **v9**). The rule that keeps the new automation
honest is written in as non-optional: **a step the nightly owns is verified at the close, never
assumed — a missing or stale report is a failure, and the close then does it by hand.**

Automation removes the labour of a step. It never removes the check.

---
*S258_BUILD_BRIEF · 15-Sep-2026 · in project knowledge, in `ClaudeCowork\03_WORKING_PAPERS\S258\`,
and loose on the SSD. Evidence for everything above is in
`ClaudeCowork\03_WORKING_PAPERS\_EVIDENCE\S258\`.*
