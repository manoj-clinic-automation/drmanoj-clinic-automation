# HANDOFF RUNBOOK — v161 · Session 229 close · 07-Sep-2026

*Supersedes v160 (S228 close). Tier 0.*

---

## §0 · WHAT HAPPENED

One long attended day, and the largest structural change the pharmacy side has had.

**Phase 0.** `D:\Downloads` was **not connected** at the open — named, requested, granted, and
nothing worked around. Manifest **389/389** from inside `KB_canon_all`; inverse check clean.
Mid-session `H:\My Drive\FinanceDB_Backups` was granted too, so the VPS's nightly database backup is
now readable without anyone copying anything.

**The export hunt (⭐2) closed.** 3,275 files walked across both drives; **822 spreadsheets opened
and identified by content**, using the project's own router signatures rather than a second opinion.
**51 unrouted Marg exports found in three folders**, two of which no brief had named. F-341's three
"missing" sale days were **never missing** — they are in those folders, and what is owed on them is
D354's ledger decision, not an export. `F:\ClinicBackup` holds zips and mirrors only.

**F-351.** `marg_rescan.py` — the tool that rescues quarantined reports — had been raising
`ValueError` on every run since the S228 `c0` change, logged as `PROBLEM: rescan=1` on **69
consecutive ten-minute cycles** and nowhere else. Two lines. The owner's own scheduler then rescued
**11 reports** unaided; quarantine 28 → 18; **zero unknowns**.

**Four signatures added** and **`MARG_REPORT_REGISTER` v1.1** written as the one live document
joining shape, cadence, route and coverage. The S203 expectations file is **retired in place**.

**The database read end to end.** 121 tables. **407 product names for a shelf of 373.** And **a
second truncation width, found only by running against real data: Marg's purchase reports clip a
description at 27 characters, the sale report at 20.**

**The item spine built, reviewed, rebuilt, installed.** v1 passed 44 self-tests and was wrong in the
one case it exists for. **v2: 54 self-tests, 0 failures**, idempotent, zero unresolved names, and the
owner installed it through one self-gating line.

**And the owner corrected the assistant four times, and was right four times.** That is the part of
this session that should be read before the next one starts.

**New fault codes:** F-351, F-352. **Decisions:** D398 … D412. **No SOP change. No
surveillance-scope change.**

---

## §1 · MENTAL MODELS — what changed in how to think about this system

**1 · An item now has a home.** `marg_item` is one row per real product and `marg_item_name` holds
every spelling it has ever worn. Everything else should reference it and define nothing. Six tables
currently hold a private idea of what an item is; that is the disease the spine exists to end.

**2 · Marg clips descriptions, and the width depends on the report.** 20 in sale, 27 in purchase.
Both are **observed facts**, stored as settings, not laws. If Marg is upgraded, re-measure.

**3 · Derived is not judged.** A price, a cost, an expected figure may be recomputed at any time and
must give the same answer. A write-off, an approval, a typed salt name may never be recomputed. They
do not belong in the same table, and today they are mixed — which is why three screens can disagree
about one item's MRP and why every total apologises for its own coverage in prose.

**4 · A pipeline that reports failures only into a log has not reported them.** `rescan=1` was true
69 times and seen zero times. A component that fails twice in a row belongs on a screen.

**5 · A message a pipeline prints is a hypothesis, not a finding.** F-352. It had printed the same
sentence for weeks and it cost the owner an export.

**6 · A green self-test suite proves the cases you thought of.** Six real defects survived 44 green
checks and were found only by an adversarial review against real data. S208's lesson, again.

**7 · The owner is a primary source.** Four times in one session he corrected a conclusion, and every
correction was checkable in data already on his disk. **Check what he says against the data before
restating what a script says.**

---

## §2 · THE LIVE BACKLOG — what S230 picks up

**⭐1 · Derivation off the screens** *(approved, needs no further word)*
One pass computes each item's price and cost once, stores it with its coverage as data, and the
screens read instead of compute. **No screen changes behaviour.** This is the step where the screens
stop being able to disagree. Then the lanes — sale, purchase, ordering, stock check — are pointed at
the spine, still with no visible change.

**⭐2 · The sheet his way** — `stock_check_06Sep2026.html` rebuilt lane-wise to match the live report
page, **born with the short row line (D399)**, with the Darpan share (5 big + 5 small/medium)
selected from it.

**⭐3 · The report page to D399** — tiles rearranged *by him*, not to a layout we choose; and the row
text cut to its core line. He deferred this until the current work is done.

**⭐4 · The adjustment-voucher engine (D388/D397)** — and it now has a first real workload: the
twelve below-zero items, two vouchers, STOCK RECEIVE.

**⭐5 · The watchers (D405/D406/D407/D409)** — the ruled cadence, the three-month expiry window, the
loud accept/reject tile for a new report. **Observing and reporting only; never writing.**

**⭐6 · The direct push from the medical PC (D402)** — after the ingestion contract is settled.

**⭐7 · The junk (D400-adjacent)** — by evidence, into quarantine, only once the shape is known.

**Also standing:** the PWA (D395/D396) · the wall card revision · the joiner reset button (F-333) ·
Google Fonts off the count page · NEFT · the loans PWA view · procedures (D373) · the S223 dawn
specs · **branching Sanjeevni/Marg into its own project when ready, taking Docterz into account**.

---

## §3 · INSTALL DISCIPLINE — one thing changed, and it should stick

**A multi-step install is multiple chances to skip the steps that are the proof.** The spine ships a
single `--install` that runs the self-tests, rehearses the whole build on a copy, writes a backup,
and only then builds — refusing at the first doubt and touching nothing if anything fails. Both
refusal paths are tested. **Prefer this shape for anything that writes to the live database.**

Unchanged and still earned: build and test offline → `py_compile` → the owner installs. A prepared
kit is proven only by a LIVE-SHAPE walk. Verify a kit gate from **inside** its own folder. **Never
run `py_compile` inside the repository** — it leaves a `__pycache__` that `.gitignore` drops
silently and the publish gate correctly refuses. It happened twice today.

---

## §4 · THE BOUNDARY — what is live, what is not

**LIVE on the VPS:** the item spine's seven tables, built and populated. **Nothing reads them.** No
screen has changed. The undo is one line, printed by the installer and recorded in the Register.

**LIVE on manojz:** `signatures.json` at 17 signatures, and the F-351 fix in `marg_rescan.py`. Both
hashed on the machine at this close.

**NOT live:** the newer `marg_spine.py` in the repository working tree (`b5956f59…`) carrying the
VINTAZ merge registration. It is **not published and not installed** and must never be confused with
what runs (`9a08b2c4…`).

**DECLARED-PENDING:** the two VPS spine pins. The owner ran the installer and pasted its closing
lines, but no `md5sum` was read from the box. **They are not passes and are re-hashed at the S230
open.**

**Owed to the owner:** nothing that requires an export. The corrections worklist is with Amir.
