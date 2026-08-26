# S180 — Marg Daily Sale: request to Marg + the target flow

**Sanjeevni Medicos · Marg ERP 9+ · prepared 15-08-2026 (Session 180)**
Supersedes `S180_Marg_Daily_Sale_Button_Settings.md`, which is folded in below.
Parents: D313 · `S179_Finance_LIVE_State` · `S180_Marg_Feed_Feasibility` · `S180_Marg_Sample_Findings`

**Nothing installed. No live file touched this session.** One new offline module built and
selftested (`marg_report.py`, 33/33).

---

## 1. What is settled — verified on real exports, not assumed

Five real exports were parsed this session. These facts are measured, not inferred:

| | |
|---|---|
| **The report** | `BILL WISE STATEMENT` with **`Report Type = Detail`**. `Summary-1` collapses it to 3 columns and loses the CASH column entirely — cash and UPI cannot be recovered from it. |
| **Columns** | `BILL NO. \| DESCRIPTION \| D.R. \| GROSS AMT. \| DISCOUNT \| TAX \| DR/CR \| NET AMT. \| CASH` |
| **Money rule** | `cash = CASH column` · `non-cash = NET − CASH`. Measured: non-cash was **36.9%** of net over 5 days. |
| **Why not the `D.R.` field** | It agrees with CASH on 133 of 138 bills — but the 5 it misses are **split-tender** bills (`.UPI` with part cash: net 3000 / cash 1000). A label cannot represent a split; the CASH column can. |
| **Credit notes** | Plain negatives (`−1150.00`). They arrive as **text** cells with leading spaces while positives are numeric — a reader trusting cell type drops every refund. |
| **Arithmetic** | Every complete day's bill rows sum **exactly** to its `DAY TOTAL`, and days sum to `GRAND TOTAL`. `GROSS − DISCOUNT + TAX + DR/CR`, rounded, reproduces `NET` per bill. |
| **Completeness test** | **A complete export always ends with a `GRAND TOTAL` row.** Its absence means the export stopped early — observed for real: month-to-date *with item detail* ran past 44 pages and truncated on day 6 of 15. |
| **Cross-validation** | 01-08-2026 was exported twice, by different runs. Both gave 37 bills, ₹28,119.00 net, ₹16,411.00 cash. Identical. |
| **Patient identity** | Marg writes `<phone> <NAME> <clinic id>` — **ID last**. `finance_ingest.split_clinic_id()` expects it first and returns `None` for every real Marg line, so all bills would land on WALK-IN. Handled upstream in `marg_report.py`. |
| **Attribution coverage** | Of 147 real bills: **77% carry a clinic ID**, 71% a phone, **82% joinable by one or the other**. The rest carry a name only. |

---

## 2. Request to the Marg team

*They connect by AnyDesk and do the work themselves, so this is written as "please set up",
not "please tell us how".*

---

> ### Sanjeevni Medicos — Marg ERP 9+ — daily sale automation
>
> We need the daily sale figures to leave this PC every day **without a staff member clicking
> anything**. Please set up the following.
>
> #### A. Two saved one-click report buttons
>
> Both are `BILL WISE STATEMENT`. They differ in three fields only.
>
> | Field | **Button A — "Daily Sale (Accounts)"** | **Button B — "Daily Sale (Detail)"** |
> |---|---|---|
> | Report From | **1st of the current month** | today |
> | To | today | today |
> | Report Type | `Detail` | `Detail` |
> | Disc.Bill Sign | `4-Bill` | `1-Bill+Item+Volume` |
> | With Item Deta. | **`No`** | **`Yes`** |
> | Day Total | `Yes` | `Yes` |
> | Cash/Cr/Disc. | `Both` | `Both` |
> | Report For | `2 Sale-S/R-Brk` | `2 Sale-S/R-Brk` |
> | Stock Less · Club Cash Sale · Add Challans | `No` | `No` |
> | Less Cr/Dr Adj. | `Yes` | `Yes` |
> | Operator Name · Patient Mobile · Pres.By Mobile | blank (all) | blank (all) |
> | Single Party · Selected Group · Selected COMPNA | `N` | `N` |
> | Column width | `80 Col` — **leave as is**, it already produces all nine columns | same |
>
> **Why two.** Button A is the accounts feed: month-to-date, so a day missed for any reason is
> repaired by the next day's file. Button B carries the medicine-level detail. They cannot be
> combined — **we tested it, and a month-to-date run with item detail exceeds the Excel export
> and truncates silently partway through.** That is the single most important thing to know
> about this report.
>
> #### B. Excel export settings — please save these with the buttons
>
> On the `SELECT DELIMETER LINE/HEADER` screen (these produced our verified files — please do
> not change them):
>
> | Field | Value |
> |---|---|
> | Select suitable seperator | `Header` |
> | Selected line as heading ? | `No` / `1` |
> | Data start from line no. | `5` |
> | Data ends at line `<0 for all>` | `0` |
> | Report in which Excel Format | `Formated` |
>
> #### C. Automatic daily generation
>
> Please schedule **both buttons to run automatically once a day**, without anyone clicking.
> We can see an empty `report\auto\` folder under each user, which suggests Marg supports this.
> Please confirm the folder and filename each will use.
>
> **Both currently write to the same file** (`D:\MARGERP\users\<user id>\report\REPORT_1.XLS`), so
> one would overwrite the other. **They must land as two separate files** — different names, or
> different folders. Please tell us the exact paths.
>
> #### D. Email
>
> Please configure Marg to **email both reports daily** to our clinic address. Note that the mail
> feature on this installation **has never been set up or used** — both mail folders are empty, so
> this is a fresh configuration, not a repair. The outgoing sender is currently the demo sender
> `MARGDEMO`; please tell us what is needed for our own sender.
>
> #### E. Two further questions
>
> 1. **Can the operator/biller be added as a column** in the `Detail` layout? Every person who bills
>    has their own Marg login, so the attribution would be reliable. Filtering by `Operator Name`
>    instead would mean one report per operator, which defeats the one-click goal.
> 2. **`up_sale` / `up_saleinfo` in the e-business cloud sync** (E.BUSID `39548`). The sync already
>    uploads masters several times an hour, but these two slots have not been written since
>    01-08-2026. What enables them, and how would we read that data from your side?
>
> Please change nothing else on this installation, and tell us afterwards exactly what was changed.

---

## 3. The target flow

```
  Marg (pharmacy PC)
        │  two buttons, generated automatically each day
        ▼
  TRANSPORT — four levels, in order of preference
        1. email to the clinic address                    ← ask D (never configured; vendor)
        2. file sits in the Marg folder, swept from there  ← the real mechanism
        3. manual report generation by a morning staff member
        4. Darpan runs it                                  ← last resort, not the design
        ▼
  marg_report.py   — refuses a file it cannot trust; never half-parses
        │  · wrong variant → refuse, naming the setting to change
        │  · no GRAND TOTAL → refuse as truncated
        │  · a day that does not sum to its own DAY TOTAL → refuse, naming the day
        ▼
  finance_ingest.adapter_csv   (UNCHANGED — "marg_export" is already registered)
        ▼
  clinic-finance
        ├── day totals: gross · discount · tax · DR/CR · net · cash · non-cash
        ├── UPI: Marg's non-cash figure vs the ICICI MPR bank email → bank is the arbiter (D313)
        ├── carry-over cash: computed by SQL view, never typed (D313)
        └── patient attribution: reads, never posts (D313)
        ▼
  DARPAN'S PAGE — checker, not maker
        · figures pre-filled; he verifies rather than types
        · carry-over cash auto-populated; he confirms the drawer
        · discount / DR-CR exceptions shown, and he explains them
        ▼
  DOCTOR + BHAWNA
        · tick off the explanations  ← the clearing action lives HERE, not with Darpan
        · daily round-off rate, trended
```

**What this changes:** Darpan moves from **maker to checker**. The machine proposes, he verifies,
the doctor disposes. That is a stronger control than the current typed entry, not a weaker one —
provided the invariants in §4 hold.

---

## 4. Design invariants

**1. Darpan sees the flags and explains them; only the doctor or Bhawna clears them.**
Visibility is deliberate — a control everyone knows about deters more than a hidden one, and he can
explain a genuine round-off far faster than we can reconstruct it. But he is the operator on most
days, so if the page ever lets him mark his own exceptions resolved, the control becomes a
formality. Kin to **D272** (self-approval barred).

**2. Flag few things, trend everything.**
Most `DR/CR` is genuine — ₹2 and ₹3 round-offs on nearly every bill. Flag per-bill only above a
threshold on **both size and proportion** (₹19 on ₹319 = 6% surfaces; ₹3 on ₹500 does not).
Separately, track **total `DR/CR` as a percentage of gross, per day**. The rate is the real
detector: a steady 0.3% is the shop's normal, and spreading discounts across many small bills makes
the rate rise rather than fall.

**3. Two confidence thresholds for patient attribution, not one.**
82% of bills join by clinic ID or phone. The remainder carry only a name, recoverable by matching
the follow-up tracker's consultation report and corroborating with the medicine names. But a name
match is a probability: for **revenue attribution** a wrong guess costs a rupee in the wrong
history; for a **discount audit** it points at the wrong patient, day and operator. All matches
feed revenue; **only high-confidence matches feed the audit.**

**4. The missing-day alarm must be verified live before the sweep is trusted.**
An unattended sweep's failure mode is silence. D313 already commits to missing days shouting — that
is the mitigation, but it has to have been *seen to fire*, not assumed.

**5. The two buttons bound the sweep's failure.**
Button B is a single day with a fixed filename: miss one sweep and that day is overwritten and
gone. Button A is month-to-date, so it repairs the money. **A missed sweep therefore costs item
detail, never the accounts.**

---

## 4A. Sale returns (credit notes) — decided

Returns are few and are accepted gracefully: the patient is asked for the purchase bill but is never
refused for not having one. **The credit note is therefore not noise to be dropped — it is a second
transaction that points at a first one**, and the system's job is to find that first one.

**Measured on the 9 credit notes in the 6-day sample:**

| | |
|---|---|
| carry at least a name | **9 of 9** — none is anonymous |
| carry name **and** mobile **and** clinic ID (the standing rule) | **5 of 9** |
| correlated back to a prior sale within the 6-day file | **7 of 9** |
| returned drugs also found in that patient's earlier sale | conclusive on one (**6 of 6 items**), partial on three |

**The two that did not match are a window artefact, not a data failure.** `CN00154` (−₹1,700, the
largest in the period) carries a clinic ID, a mobile *and* a name — its original sale simply predates
the file. **The lookup therefore runs against the database, not the day's file**; `finance.db`
already holds 121 imported days.

**Design:**

1. **Counter rule stands** — every return bill carries patient name, mobile and clinic ID. The system
   now *measures* compliance (5 of 9 today), so it becomes a staff number rather than an instruction.
2. **Reception lookup and next-day reconciliation are the same index**, run in opposite directions:
   reception searches sales to find a patient's bill; reconciliation searches sales to find a
   return's origin. Build it once.
3. **Correlation is by clinic ID → mobile → name**, then corroborated by the returned **medicine
   names** against that patient's earlier sale. Item detail (Button B) is what makes the
   corroboration possible; without it there is a patient but no proof.
4. **The flag is not "a return happened."** It is **large, and still unmatched after the database has
   been searched** — the `CN00154` shape. A small, matched return needs no attention.
5. **Timing: next day, with the daily feed.** No real-time requirement, so nothing has to run at the
   counter.

*Why this matters beyond bookkeeping: a return is cash out of the drawer with no goods trail unless
something checks it. Correlating to a real prior sale, and to the specific drugs on it, is what makes
a fictitious return hard.*

**Consequence for the build:** `finance_ingest.adapter_csv` skips rows with `amount <= 0`, so credit
notes would never reach the database at all. That filter has to be addressed before any of the above
is possible — it is no longer an open question but a required change.

---

## 5. Still open

| # | Item | Owner |
|---|---|---|
| 1 | Everything in §2 — the whole vendor request | Marg, by AnyDesk |
| 2 | One export from **each** button, sent for checking before the buttons are saved | owner |
| 3 | ~~credit notes: decision needed~~ → **DECIDED, see §4A.** Credit notes are captured and correlated. The `adapter_csv` `amount <= 0` filter must be addressed — this is now a required change, not an open question | build |
| 3b | Return-correlation lookup over `finance.db` (clinic ID → mobile → name, corroborated by medicine names), serving reception live and reconciliation next-day | build |
| 4 | `ABL` appearing where the phone sits — is that a credit/party account? If so those bills are credit sales, a third category beyond cash and UPI | owner |
| 5 | `pip install xlrd` on the VPS — new dependency for reading legacy `.xls` | install |
| 6 | Home-medicine vs procedure-medicine classification by medicine name (Button B data) | design |
| 7 | Flag thresholds in §4.2 — actual rupee and percentage values | owner |

---

*Built and tested offline. `marg_report.py` py_compile clean, selftest 33/33, run against five real
exports. `finance_ingest.py` is NOT modified. Sample exports carry patient names and phone numbers
and stay in the session workspace only — never in project knowledge, the repo, or a git kit
(F-31/F-49).*
