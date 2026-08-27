# HANDOFF RUNBOOK — v140 · Session 206 close · 27 August 2026 IST

**Tier 0.** §0 what happened · §1 mental models · §2 the open backlog · §3 install discipline ·
§4 the boundary. **§2 is the close-time snapshot; `OWNER_TODO_LIVE.md` is the always-current
truth, and each points at the other.**

---

## §0 — WHAT HAPPENED AT S206

**A full build EOS. Two kits published and verified (`228c40f..25d3730`, 60 files, 4,983
insertions); no live file on any machine was changed.**

**The work.** Every item Sanjeevni stocked between 1-Apr-2026 and 26-Aug-2026 was reconciled
against both stock counts. **285 items moved; 239 balance exactly; the residue is 1,769 units —
0.98 % of the 181,232 units that passed through the shop.** All 46 unbalanced items carry a named
cause: **GOODS_IN 15 · RENAMED 8 · GOODS_OUT 11 · ZEROED 8 · OFF_LIST 4.** No "other" bucket, no
UNEXPLAINED item.

**Three faults in the READING, none in the data — and all three were ours.**
**F-225** whole-unit sales read as zero (2,807 lines, 16.3 % of the year — six items reported as
dead stock while selling normally). **F-224** credit notes subtracted instead of added, which makes
the error twice the quantity and is how it was caught (376 lines, 3,082 units). **F-223** the sale
report truncates item names at 20 characters, so sales attach to codes owning no stock (11 codes,
largest 574 units) — **and the obvious `len(name)==20` test misses the biggest cases, because the
cut can land on a space that is then stripped.**

**None of the four existing cross-checks caught any of them** — bill chain, four-way purchase,
`WHOLE = MAIN+DTH+SCRAP`, multi-store identity. All four kept passing. **Only forcing every item to
account for itself found them.**

**The owner named both missing movement types**, which the reconciliation could isolate but not
explain: **F-228** stock removed by editing the quantity in place — *"I open the stock, press a
keyboard command and alter the stock quantity and expiry"* — **which writes no voucher and so
appears in no export**; and **F-229** Ravi Medical with **no purchase bill at all in May or
August**, goods in custody, paperwork absent.

**Also:** 79 duplicate item-code pairs mapped (7 to merge, 61 stubs, 10 to check, 7 to leave) ·
77 renames generated to fit the 16-character bill print with every size and strength preserved and
zero collisions (**F-230**) · 12 items holding 40 units on no current item list (**F-231**) ·
the two stock lists diffed (only six items held stock and vanished; five are naming).

**Both Sanjeevni kits were renamed before first commit** — free then, expensive after — and the
rename would have broken `ingest.py` silently. **`SANJEEVNI` is the tag for every pharmacy artefact
from here.**

**The F-100 gate earned its keep.** `PUBLISH_ALL.bat` refused the publish over
`live_pins_IGNORE_block.tsv`, caught by `.gitignore:40 *.tsv` under the PATIENT-DATA block — a kit
file that would have left the repo silently. **Resolved by renaming the file to `.txt`, not by
weakening the gate.**

**A self-contained session kit** was built at `D:\Downloads\S206_SANJEEVNI_SESSION_KIT\` — 190
files, 11 MB, including **46 raw Marg exports**. It rebuilds every figure with no project
knowledge, no chat history and no GitHub.

**New fault codes:** F-223 … F-231, all **candidates** — the F-series fork is unratified.
**SOP changes:** none. **Surveillance scope:** unchanged.

### ⚠ A GAP IN THE PREVIOUS CLOSE, FOUND BY MEASUREMENT AT THIS ONE

**§S205 IS ABSENT FROM THE KB HISTORY ARCHIVE.** The S205 close produced
`HANDOFF_RUNBOOK_2026-08-27_Session205close_v139.md` (step A3) but **never ran A1 or A2** — the
Archive stayed at v1.51/S204 and the Register at v5.56/S204. **S205's history is unarchived and is
NOT reconstructed here.** Writing another session's narrative from its leftover working documents
would be authoring history from second-hand text, which A0 and D172 forbid. **It needs the owner's
ruling: reconstruct it from the S205 documents, or record it as permanently lost.**

---

## §1 — MENTAL MODELS

- **A check that has never failed may be answering a question nobody is asking.** Four cross-checks
  passed through all three S206 faults. The F-195 / F-209 / F-215 shape, one layer out.
- **A pack size is never assumed.** `2:3` is 23 tablets at `1*10` and 33 at `1*15` — wrong by a
  *multiple*, not a rounding. Convert with the packing printed on the row itself.
- **A size that was never recorded is never invented.** Where six belt sizes cut to the same
  characters, the sale pools at the family and says so. Inventing a size to make a line balance is
  the worst outcome available.
- **An edit that writes no voucher is invisible to every report, and the absence of evidence is
  the evidence.** A batch only ever removed appears on no line anywhere.
- **`loose_qty` is authoritative for purchases** — Marg computes it with the pack size at the time
  of the bill while reprinting the current packing beside it.
- **Rename before the first commit.** Free while untracked; history to rewrite afterwards.

---

## §2 — THE OPEN BACKLOG (close-time snapshot · live truth is `OWNER_TODO_LIVE.md`)

**Clock items:** the August close (first fully live enforced run) · **Pravesh exits 31-August**,
the first run of the standard exit system.

**🔴 Token rotation — four `FINANCE_*` values printed in chat at S206, six stores not five.**

**Owner rulings owed:** §S205's archive gap (above) · the 12 items on no item list (write off or
restore) · `ETOZOX 90` physically counted, ask Amir first · the Ravi May and August bills ·
`FINGER COT M` vs `FINGER COT M TYNOR` · shortening the belt/immobiliser names inside Marg ·
the private store for the 24 F-216 CAP files · the IGNORE-rows question · **ratify or renumber
F-218 … F-231** · VINBACTUM DS · DTH's future · the uncredited-return ageing threshold ·
Design Language v1.1's dark palette.

**Build queue:** the July settlement line · Darpan's form (maker → verifier, with the last sale
bill number filed alongside the count) · the medical verifier, reporting-only · the standard exit
system · the dead-man's alarm · **Q2 `VERIFY.bat` for the reinstall kits** (the only queue item
still open) · then F-183 · F-178 · Staff Console Phase 0 · Purchase Portal D335 · August NEFT ·
Amir's weekly set · Club-4.

**Sanitisation plan (10 steps) is written** — `S206_MARG_SANITISATION_AND_DUPLICATES` §5. **Step 2
is the one that matters**: raise a stock-adjustment voucher instead of editing the quantity.

---

## §3 — INSTALL DISCIPLINE

Unchanged. Build/test offline → `py_compile` → the owner installs. **Nothing live was rebuilt this
session and no live file moved**, so no pin moved and A11 has nothing to capture.
`PUBLISH_ALL.bat` remains the one publisher (F-212) and clears its own stale locks (S195 sweep) —
**do not hand the owner a bare `git` command; `where git` fails on manojz, which is why that batch
file carries four fallback paths.**

---

## §4 — THE BOUNDARY

The assistant runs the whole close. The owner's residual work is **one `PUBLISH_ALL.bat`
double-click** and the on-box pin-list copy. The VPS stays owner-only by design — every credential
lives with him.

---
*HANDOFF_RUNBOOK v140 · S206 close · supersedes v139.*
