# S180 — Marg feed: action register

**15-08-2026 · Session 180 · Sanjeevni Medicos (medical unit)**
Companion to `S180_Marg_Feed_Request_and_Flow.md` (the request text + the flow) and
`S180_Marg_Sample_Findings.md` (the evidence). Reference items by their ID.

**Status:** nothing installed, no live file touched. One offline module built (`marg_report.py`,
py_compile clean, selftest 33/33, run against five real exports).

---

## V — VENDOR TASKS (Marg team, by AnyDesk)

| # | Task | Notes |
|---|---|---|
| **V1** | Save **Button A — "Daily Sale (Accounts)"** | month-to-date · `Report Type = Detail` · `With Item Deta. = No` · `Disc.Bill Sign = 4-Bill` · `Day Total = Yes` · `80 Col` |
| **V2** | Save **Button B — "Daily Sale (Detail)"** | today only · `Report Type = Detail` · `With Item Deta. = Yes` · `Disc.Bill Sign = 1-Bill+Item+Volume` |
| **V3** | Save the Excel **delimiter/header** settings with both buttons | `Header` · heading `No`/`1` · data starts line `5` · ends `0` · `Formated` |
| **V4** | Make the two buttons write to **separate files** | they both write `REPORT_1.XLS` today — one overwrites the other |
| **V5** | **Schedule both to run automatically, once daily** | an empty `report\auto\` folder exists per user, suggesting this is supported |
| **V6** | **Configure email** of both reports to the clinic address | the mail feature on this install has **never been set up** — fresh configuration, not a repair |
| **V7** | Generate the **historical item-wise bill ledger** — **ONE FILE PER MONTH** | **not one file "till date".** See the warning below. |
| **V8** | Enable **`up_sale` / `up_saleinfo`** in the e-business cloud sync | E.BUSID `39548`; dormant since 01-08-2026 while masters sync hourly |
| **V9** | Add the **operator/biller as a column** in the `Detail` layout, if supported | every biller has their own login, so attribution would be reliable |

> ### ⚠ V7 — the one thing that must not be got wrong
> A month-to-date range **with item detail** was tested on 15-08-2026. It ran past 44 pages and
> **the export truncated at day 6 of 15 — silently.** The file opened, the rows were there, only the
> `GRAND TOTAL` was missing. A request for months of item-wise history in a single file will fail the
> same way and will look complete.
> **One file per calendar month, each ending in its own `GRAND TOTAL` row.** Each file is then
> independently checkable, and "did we get everything?" becomes pass/fail instead of a judgement.

---

## Q — VENDOR QUESTIONS (we need answers, not actions)

| # | Question |
|---|---|
| **Q1** | The exact **folder and filename** each scheduled button will write to. |
| **Q2** | Can a saved button set its **date range automatically** (1st of current month → today), so no one types dates? |
| **Q3** | Can the output file be **date-stamped** rather than overwritten? *(Not a blocker — Button A is month-to-date, so a later file always contains everything an earlier one did.)* |
| **Q4** | Outgoing sender is the demo sender **`MARGDEMO`**. What is needed to use our own sender? |
| **Q5** | What **enables `up_sale`/`up_saleinfo`**, and **how would the clinic read that data** — Marg Books portal, an API, or a scheduled cloud export? |
| **Q6** | Does a **credit note have a reference field** we can write a return-authorisation code into? (If not, can it go in the description?) — see **U6**. |
| **Q7** | Is there a **page or line cap on the Excel export**? This is what truncated our month-to-date-with-items file. If it can be lifted, V7 gets much simpler. |
| **Q8** | Afterwards: **exactly what was changed** on this installation. |

---

## O — OUR TASKS (owner / clinic side, no code)

| # | Task | Blocks |
|---|---|---|
| **O1** | Send the §2 request (V + Q above) to Marg | everything vendor-side |
| **O2** | **One export from EACH button → to me for checking BEFORE the buttons are saved.** `Disc.Bill Sign` is moving to an untested value; if the layout shifted we fall back to `2-Bill+Item` | V1·V2 |
| **O3** | **One complete Button A export, 01-Aug → date, passing its GRAND TOTAL check** | **gates the August cutover** — see the note below |
| **O4** | Confirm whether **`ABL`** (seen where the phone sits) is a credit/party account. If so those are **credit sales** — a third category beyond cash and UPI | U2 |
| **O5** | Set the **flag thresholds**: rupee amount and % of bill, for `DISCOUNT` (primary) and `DR/CR` (secondary) | U9 |
| **O6** | Counter rule: **every return bill carries name + mobile + clinic ID.** Currently **5 of 9** | U3 |
| **O7** | Decide the **return-reason dropdown**, and which reasons route **clinically** to the doctor rather than into finance | U5 |
| **O8** | **See the missing-day alarm actually fire** before the unattended sweep is trusted | U12 |
| **O9** | Look at **`A002783`** — gross ₹85.39, `DR/CR` −₹85.00, **99.5% written off**. Almost certainly innocent; it is the shape a flag exists to surface | — |
| **O10** | *Carried from S179:* commit `gitkit_S179.zip` — **`.gitignore` the PHI paths in the SAME commit, before `git add`** (F-31/F-49) | — |

> ### O3 — what August actually rests on
> Verified Marg data today covers **01–05 August** (plus 01 and 15 Aug singly). **06–14 August was
> inside the export that truncated and has been validated by nobody.**
>
> `finance.db` already holds the legacy import for **Apr 1 → Aug 13** from the Sheet. So for 01–13
> August there would be **two independent sources for the same days** — a real reconciliation, not a
> substitution. That matters, because S179 recorded the legacy import carrying **14 missing days and
> 7 negative-cash days**. Marg has the bills the Sheet did not, so this export is the thing that can
> close those gaps rather than merely avoid re-typing them.

---

## U — OUR MODIFICATIONS AND UPGRADES (build)

### ✅ DONE — installed and verified

| # | Item | Evidence |
|---|---|---|
| **U1** | **Sale returns reach the books.** The `amount <= 0` junk filter no longer eats credit notes. Returns store as a positive `amount_p` with `service='<base>_return'`; `v_day_attribution` nets them | installed 15-08-2026 20:38 IST · smoke **INGEST 50/50** · `sso_epoch_ok: true` · 121 days intact |
| **U2** | **`marg_report.py`** — reads the Marg `.xls`, refuses what it cannot trust (wrong variant · truncated · a day that fails its own arithmetic), emits bill rows and drug rows | installed 15-08-2026 21:14 IST · **selftest 64/64** offline, 38/38 on the box (sample `.XLS` deliberately not shipped) |
| **U3** | **`finance_returns.py` + `sale_line_item`** — drug lines get a home; a credit note is traced to its sale by patient, corroborated by the medicines returned. Graded verdict, never a refusal | same install · **RETURNS 28/28** · table additive, proved to add 6 objects and remove none, re-run a no-op |
| **U4** | **Expiry + 30-day window rules** — folded into U3 as flags (`expired_or_expiring`, `outside_return_window`), driven by settings not code | in the same module |
| **U10** | **Two confidence thresholds** — partly done. `marg_report` now scores a clinic ID: 4 digits (111 of 113 real IDs) is trusted at 0.95–0.99; anything else scores below finance's `min_confidence` 0.70 and goes to review. U3's verdicts are graded so only `conclusive` is fit for an audit | in both modules |
| **U13** | **`xlrd`** installed on the VPS | `xlrd 2.0.2` |
| **U1-fix** | **Resolving a queued sale RETURN no longer 500s.** U1 stores queued returns signed; `sale_item` forbids negatives; `/finance/api/review/<id>/resolve` was passing the signed value straight in. Now converted to a magnitude + `_return` service on the way out | installed 15-08-2026 22:13 IST · **SMOKE 179/179** · proved BEFORE HTTP 500 / AFTER HTTP 200 `('pharmacy_return', 7700)` |
| **U11** | **`finance_identity.py`** — proposes a patient for lines that arrived with only a name, from the system's own accumulated roster. Grades `corroborated · unique_exact · near · ambiguous · none`. **Proposes; never assigns** | same install · **IDENTITY 44/44** |

**U11's measured ceiling — read before expecting more from it.** Roster of 94 patients from six
days, against the 36 lines with a name but no clinic ID: **1 corroborated, 2 unique, 2 near,
0 ambiguous, 31 none — 3 of 36 safe to offer as a default.** Of the 31 unmatched, **29 are distinct
names**; only one repeats. They are one-off walk-ins, not clinic patients whose ID was missed.

**That reframes the 82% attribution figure: it is not a defect to engineer away, it is roughly the
share of pharmacy business that is clinic patients at all.** The other ~17% (₹19,979 over six days)
is counter trade. Do not spend effort on cleverer name matching — the ceiling is set by who walks
in. The only thing that would raise it is a roster independent of the pharmacy typing the ID: the
follow-up tracker's consultation report, which lives on the clinic PC. That is a transport problem.

**Self-caught during the build, worth recording:** `marg_report`'s CSV was emitting **full 10-digit
phone numbers**. `patient_ref` stores `phone_last4` and nothing more, and `ingest_column_map` has no
phone field at all — so that was a fuller exposure than both the schema's intent and the standing
masking rule. The bill CSV now carries last-four only; the item CSV carries no patient identity at
all. Outputs were grepped for any 10-digit string: none.

**Real-data proof of U3**, run end-to-end over the six-day export:

```
CN00158  conclusive    6 of 6 medicines matched, 2 days earlier
CN00152  conclusive    1 of 1
CN00153  conclusive    1 of 1
CN00157  conclusive    1 of 1
CN00151  patient_only        CN00154  none + large_and_unmatched   <- the Rs 1,700 one
CN00155  patient_only        CN00159  none
CN00156  patient_only
```

**Proved on a Marg-shaped file:** before, 2 rows kept and the day attributed ₹2,150.00; after,
3 rows kept and ₹1,750.00. The refund was ₹400 — the old code overstated the day by exactly that,
silently.

**Why not simply allow negative amounts.** `sale_item.amount_p` is declared `CHECK (amount_p >= 0)`
and SQLite cannot drop a CHECK with `ALTER TABLE`. Removing it meant create-copy-drop-rename on a
live table holding 121 days of real patient data — a data migration, to change a *reporting*
behaviour. Storing the magnitude and putting the direction in `service` honours the invariant the
schema author chose and **touched no table and no row**; only one view changed. `sale_item` was
first confirmed to be summed in exactly one place, so a return has nowhere else to leak into.

> **Install-order enforced by the test, not by memory.** The smoke test contains a check that fails
> if the view migration was not applied, and the smoke test is the install gate. Verified: against
> an un-migrated database it gives **49/50, exit 1**. The code therefore cannot be installed against
> an un-migrated store.

**⚠ RECORD-KEEPING OWED AT CLOSE-OUT — the full live-state delta for this session:**

| Live artefact | Change |
|---|---|
| `/root/finance/finance_ingest.py` | `872ec33ef7c628cd474224b0c6c78ba5` → **`2cd0f264fb1a091f3e3ec7c3f4a17438`** |
| `/root/finance/marg_report.py` | **NEW** — `28b47d447cfd966411742055717a5c56` |
| `/root/finance/finance_returns.py` | **NEW** — `a46a87e65d951d59baeb9d86c9d8fe59` |
| `/root/finance/finance_returns.sql` | **NEW** — `9cec4e317590f845beda87881721cf69` |
| `/root/finance/finance_app.py` | `61e36d5522e4e99e1e65e159ef50c85e` → **`7b62b7ae661914505c864d71cc6c9abc`** |
| `/root/finance/finance_identity.py` | **NEW** — `81092e3ca18c9a85f1de06cc8055d967` |
| `finance.db` · view `v_day_attribution` | redefined to net `*_return` services |
| `finance.db` · table `sale_line_item` | **NEW**, plus 4 indexes and 3 `returns.*` settings |
| VPS python | **`xlrd` 2.0.2** added (system `python3`) |
| Backups taken | `finance.db.bak_20260815_203810` · `finance.db.bak_20260815_211437` · `finance_ingest.py.bak_20260815_203810` |

| | |
|---|---|
| KB Register live-file table | **stale** until bumped — next session's Phase 0 will otherwise halt on the mismatch |
| Session type | **FULL**, not EOS-light — live VPS code, a live view, and a new live table |
| Git | none of the above is committed yet. `gitkit_S179.zip` is *still* uncommitted (O10), so the repo is now two sessions behind. **`.gitignore` the PHI paths before the first `git add`** (F-31/F-49) |
| Decision candidate **D314** | *A sale return is stored as a magnitude with its direction in the row's type, never as a negative amount, so a live store's non-negative invariant is honoured without a data migration.* Reusable when clinic and lab replicate — belongs in the decisions index, not only in a commit message. |
| Decision candidate **D315** | *A patient-identity match is graded, and only the top grade may feed an audit.* Revenue attribution tolerates a probable match; a discount or return audit does not, because a wrong match names the wrong patient, day and operator. |
| Finding candidate **F-85** | *Session-numbered artefacts were labelled with a forward number before the session that would carry it had opened* (`S180_Marg_Folder_Recon` written during S179; the feed survey then calling itself S181). Kin to D188. |
| Finding candidate **F-86** | *A reader built for a PHI source emitted full phone numbers because it was written against the report's shape, not against the destination schema's masking rule.* Self-caught before install. The destination's constraints are part of the spec. |
| Finding candidate **F-87** | **A change was shipped to a test suite that could not be run offline — twice.** `finance_app.py`'s smoke suite is written against the real store (>100 filed days, approved/locked days, open exceptions, a legacy tail leaving cash negative), so it could not run here. That was treated as acceptable and the change shipped on reasoning alone. It failed on the box, and the install gate rolled it back correctly. Kin to **F-84** — *the offline-testing shortcut was the vulnerability* — which this project had already minted and which was repeated anyway. **The remedy is an asset, not a resolution:** `dev_seed_smoke_db.py` builds a database satisfying the suite's preconditions, so the suite runs before shipping. Verified differentially (unmodified 163/173 vs modified 166/176 on identical seeded data — zero failures added) before the third build was sent. **RULE: if a test suite cannot be run, making it runnable is the first task, not an optional one.** |
| Finding candidate **F-88** | *A passing `md5sum -c` proves a kit is internally consistent, not that it is the intended kit.* A stale download's checksums match its own files, so the gate passed twice on an old build. Kin to **D188**. Fixed by having the installer carry the identity of the build it belongs to and refuse to run otherwise. |
| Trap, now documented in code | `ingest_day` **supersedes** the day's previous batch and **deletes** what it produced. Any test that ingests destroys what earlier tests set up. Cost two separate debugging rounds this session. |

### U-now — no vendor dependency, can start immediately

| # | Item | Size | Why now |
|---|---|---|---|
| ~~U1~~ | ~~`adapter_csv` skips `amount <= 0`~~ | — | **DONE — see above.** Sized "small" and it was not: the database constraint made it a schema question. Sizings below are re-checked against the actual schema before being quoted. |
| ~~U2~~ | ~~item lines from the reader~~ | — | **DONE.** Credit-sale category still owed once **O4** answers what `ABL` is |
| ~~U3~~ | ~~return-correlation lookup~~ | — | **DONE** |
| ~~U4~~ | ~~expiry + 30-day rules~~ | — | **DONE**, as flags driven by settings |
| **U5** | **Reception return page**: patient details + drugs + reason dropdown → **printout** handed to Darpan with the medicines | medium | the separation-of-duties control |
| **U6** | **Return-authorisation reference code** on that printout, entered into the Marg credit note → next-day correlation becomes **exact instead of probabilistic** | small | depends on Q6 |
| **U7** | **Discount deduction at return** — from the original bill's `DISCOUNT` (primary) and `DR/CR` (secondary) | **medium, re-sized** | **the discount is not stored anywhere yet.** `sale_item` holds only `amount_p` (NET); `adapter_csv` reads no discount column even though `ingest_column_map` permits one. So this needs the discount carried through *and* somewhere to put it (`ALTER TABLE ... ADD COLUMN` is O(1) metadata in SQLite and safe, but it is a schema decision, not a code tweak). Sized after reading the schema, not before |
| **U8** | **Darpan's page**: figures prefilled, carry-over cash auto-populated, exceptions shown with an explanation box. **He explains; he cannot clear** | medium | D272 kin |
| **U9** | **Flag engine**: per-bill flags above a threshold on **size AND proportion**, plus the **daily discount rate, trended** | medium | needs O5 |
| **U10** | **Two attribution confidence thresholds** — all matches feed revenue, only high-confidence matches feed the audit | small | |
| **U11** | **Name matching** against the follow-up tracker consultation report, corroborated by medicine names — recovers the ~14% of bills with a name only | medium | |
| **U12** | **Transport**: folder sweep, and email ingest if V6 lands | medium | needs O8 first |
| **U13** | **`pip install xlrd`** on the VPS — new dependency for reading legacy `.xls` | trivial | install-time |
| **U14** | **Home-medicine vs procedure-medicine** classification by medicine name | medium | Button B data |

> ### U7 — a correction to an earlier working assumption
> The discount channel is the **`DISCOUNT` column**, not `DR/CR`:
> ```
> 138 sale bills · with a DISCOUNT value:  84   total  ₹3,634.00   (~3% of gross)
>                 · with a DR/CR    value:  16   total     ₹199.00   ( 0.16%)
> ```
> An earlier draft built the flag design around `DR/CR` because that is where the first large single
> value appeared. `DISCOUNT` is the real channel by a factor of eighteen. **Flags and the daily rate
> track `DISCOUNT` first; `DR/CR` is secondary.**
>
> This also makes the return-deduction point larger than it first looked: if ~3% is discounted on six
> bills in ten, a return processed at list price systematically refunds more than was taken.

### U-blocked — waiting on the vendor

| # | Item | Waiting on |
|---|---|---|
| **U15** | Ingest of the scheduled/auto-generated files | V4·V5·Q1 |
| **U16** | August reconciliation: Marg vs the legacy Sheet import, repairing the 14 missing days | O3 |
| **U17** | Historical item-wise backfill | V7 |
| **U18** | Cloud-sync route, if `up_sale` is enabled | V8·Q5 |

---

## Suggested build order for "meanwhile"

Everything in **U-now** is genuinely independent of Marg. Recommended sequence, because each unlocks
the next:

1. **U1** — the `amount <= 0` filter. Nothing about returns can exist until credit notes reach the
   database. Smallest change, largest unblock.
2. **U2** — item lines out of the reader, so U3's medicine corroboration has data.
3. **U3 + U4** — the correlation lookup and the return rules. Buildable and testable offline against
   `finance_schema.sql`, which is in the git kit.
4. **U7 + U9 + U10** — the discount deduction, the flag engine, the confidence thresholds.
5. **U5 + U6 + U8** — the reception page, the reference code, Darpan's checker page.

*Steps 1–3 need nothing from anyone. Step 4 needs O5 (your thresholds). Step 5 needs O7 (the reason
vocabulary) and Q6 (whether Marg has a reference field).*

---

*Sample exports carry patient names and full phone numbers. They stay in the session workspace —
never in project knowledge, the repo, or a git kit (F-31/F-49).*
