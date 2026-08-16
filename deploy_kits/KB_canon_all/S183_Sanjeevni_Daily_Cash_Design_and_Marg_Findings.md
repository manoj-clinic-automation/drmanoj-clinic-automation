# S183 — Sanjeevni daily cash visibility: design + what the five months of Marg data actually show

**Session 183 · 16 Aug 2026 · Dr. Manoj Agarwal Clinic, Bareilly**
**Status: DESIGN + EVIDENCE. Nothing built, nothing installed, no live file touched.**
Companion to `S180_Marg_Feed_Transport_Design`, `S180_Marg_Sample_Findings`,
`S179_Finance_LIVE_State`. Supersedes nothing.

**PHI:** every figure below is a count, a date or a rupee total. No patient name, number or
bill row appears anywhere in this document. The source exports stay on the PC and in the
session workspace only — never the repo, never a git kit (F-31/F-49, D320).

---

## 1. The need, stated as the owner stated it

> *"Daily cash drawer visibility is a need, not attainable in the current system."*
> *"Daily visibility of Sanjeevni cash is not visible to me."*

Three attempts have been made and each failed in a different place:

| Attempt | Where it failed |
|---|---|
| Google Form | friction at the staff end — cumbersome to fill |
| Connected Google Sheet | a chore for the owner to open and follow |
| GAS projects emailing out | emails scratchy; the detail got buried |

The common fault is that **each attempt moved the effort somewhere rather than removing it**,
and the answer always ended up somewhere the owner had to go and look for.

**The target:** the owner opens one place and sees how much cash is with Darpan today, and that
number is *derived* rather than *claimed*.

---

## 2. The control that makes the number trustworthy (owner's decision, S183)

**The morning Marg export is run by Shavez or reception staff — not by Darpan.**

The reliability gain is secondary. The real gain is **segregation of duty**: the person who
holds the cash is no longer the person who produces the record of what was sold.

- Reception/Shavez → produces *what was sold* (the Marg export).
- Darpan → declares *what was collected*, by tender, and his drawer.
- ICICI → arbitrates the non-cash side.
- Owner → sees the residue, and approves expenses and advances.

Any gap becomes visible arithmetic rather than an accusation. Nobody has to be suspected for the
system to work, which is what makes it survivable in a small practice.

---

## 3. The daily identity

```
        Marg NET (all bills, credit notes already negative)
      − HOME-MEDICINE bills            (billed, never collected — see §5.2)
      = COLLECTABLE

        COLLECTABLE = cash + UPI + card
                             └─────┬────┘
                        both settle through the SAME ICICI POS
                        → the bank arbitrates the entire non-cash side

        cash on hand  =  opening
                       + cash collected
                       − drawer expenses        (Darpan posts, owner approves)
                       − advances taken         (Darpan posts, owner approves)
                       − bank deposits
                       =  closing   → becomes tomorrow's opening
```

Two properties follow, and both matter:

- **Cash becomes derived, not asserted.** Once the bank fixes the non-cash side and Marg fixes
  the collectable, cash is the remainder. That is what "the cash then remains verified" means in
  practice.
- **Cash on hand is a CHAIN.** A missed day breaks it, and every figure after the gap is wrong
  until someone repairs it. This is the strongest argument for a **month-to-date export**: any
  single run sweeps up every missed day automatically, so the chain self-heals no matter who was
  on leave. One click either way.

**Medical tenders (owner, S183): cash and UPI only. Never Razorpay. A card is swiped rarely, on
the same ICICI POS machine.** So no Razorpay stream is needed for this unit, and card + UPI
reconcile against one bank source.

---

## 4. What the five months of Marg data prove

**Source:** 8 exports covering **1 Apr → 15 Aug 2026**, read with the live `marg_report.py`
(md5 `28b47d447cfd966411742055717a5c56`, verified against the box at S183).
**124 distinct business days, zero overlap between files, 3,162 bills, 16,118 item lines.**

```
NET      2,748,671.00
CASH     1,980,916.00   (72.1%)
NON-CASH   767,755.00   (27.9%)
```

Every file passed the parser's own arithmetic self-checks — each day summing to `DAY TOTAL`,
each file ending at an intact `GRAND TOTAL`.

### 4.0 THE decisive cross-check: Marg vs Darpan's own filing (S183)

The 121 legacy days already carry Darpan's Google-Form declaration (`day_line`, cash/upi/card,
imported at S179). Joining that against the Marg export on the 119 shared days gives two fully
independent records of the same days. The result governs the whole design:

| Comparison | Marg | Darpan | Verdict |
|---|---|---|---|
| **Day total** | 26,54,543 | 26,47,321 | **agree to 0.3%** — 118 of 119 days within ₹2,000 |
| **Cash figure** | 18,99,768 (72%) | 17,67,393 (67%) | Marg **overstates cash by ₹1,32,375** |

Two conclusions, both load-bearing:

1. **Marg is authoritative for the TOTAL and only the total.** Independent agreement to a third of
   a percent means the feed is trustworthy for revenue and the historical filing was honest — the
   backfill will reconcile cleanly. **The single day over ₹2,000 apart is 12 June** (Marg 23,252 vs
   Darpan 14,765, +8,487) — isolated, worth one look, not a pattern.
2. **Marg's CASH column must never be used as the cash figure.** It is wrong by ₹1.32 lakh over the
   period. The cash/UPI split can come only from Darpan's declaration, arbitrated by the bank. This
   is the empirical proof that the human-declares-the-split design (§3) is necessary, not
   ceremony — the shortcut of trusting Marg's cash column would have been ₹1.3 lakh wrong.

**The variance alarm now has a measured threshold, not a guessed one:** a live day whose Marg total
and Darpan-declared total differ by more than ~₹2,000 escalates to the owner. 118 of 119 historical
days clear that bar.

*Home-medicine nuance: Marg includes home-medicine as revenue+cash (§5.2), yet the totals still
agree to 0.3% — so Darpan's totals appear to already absorb it rather than it opening a systematic
gap. Whether it is paid-on-delivery or simply counted is a question for him; it does not change that
home bills must stay visible (§5.2).*

### 4.1 Two practice changes, both visible in the data

| Month | Bills | Patient identity captured | Cash share |
|---|---|---|---|
| Apr 2026 | 702 | **0%** | 86% |
| May 2026 | 677 | **0%** | 73% |
| Jun 2026 | 718 | 33% | 63% |
| Jul 2026 | 710 | 87% | 70% |
| Aug 2026 (to 15th) | 355 | 82% | 66% |

**Patient identity capture began on 19 June 2026.** Not one bill before that date carries a
phone number or a clinic ID. 19 Jun = 30%, 20 Jun = 85%, then 75–100% steadily. That is a
practice starting and bedding in within two days.

> **Consequence:** roughly **1,700 bills from 1 April to 18 June have no patient identity at
> all** and will attribute to WALK-IN. This is not a fault and is not recoverable — it is simply
> when the practice began. Expect the first half of any patient-level analysis to be empty.

### 4.2 The 100%-cash window is an EVENT, not a habit

**21 April → 6 May 2026 · 14 trading days · 364 bills · ₹3,03,035 · 99.2% labelled cash.**

> **SETTLED at S183 by the §4.0 cross-check — no memory required.** Darpan's own Google-Form filing
> declares **₹84,613 of UPI across these same 14 days** that Marg labelled cash (e.g. 25 Apr: Darpan
> 51% UPI; 2 May: 58% UPI). So the window was **not** cash-only — UPI was collected and Darpan
> recorded it correctly; **Marg simply stopped writing the UPI split into its CASH column for two
> weeks.** The earlier ₹95k estimate from a rate is now a measured ₹84,613. The open question "what
> changed on 21 April" is answered at the level that matters: it was a Marg-recording gap, already
> caught by the independent human record, not a real cash surge and not a loss.

The window has a clean edge on both sides:

```
20 Apr   ₹24,879   87% cash     ← UPI recording working
21 Apr ─────────── window begins ───────────
 6 May ─────────── window ends  ───────────
 7 May   ₹16,770   77% cash     ← UPI recording working again
```

At the 31.3% non-cash rate every other day runs at, roughly **₹95,000 of that window is sitting
mislabelled as cash**. *That is an estimate from a rate, not a measured fact.*

> **This is not a training problem.** UPI was being recorded correctly on both sides of the
> window. Something changed on 21 April and was put right on 7 May. **The question to ask is
> "what changed on 21 April?"** — a QR code swapped, the machine moved, a different person on the
> counter. Fourteen bounded days is small enough that someone will remember.
>
> A settled cross-check is available and needs no new code: those days already have `day_entry`
> rows carrying Darpan's own Google-Form cash and UPI figures. **Comparing his filed split
> against Marg's cash column for those 14 days would settle it outright.**

### 4.3 Isolated later days

Outside that window only three all-cash days have enough bills to be meaningful: **10 July**
(12 bills), **11 August** (25 bills) and **14 August** (23 bills). The remainder are 1–3 bill days
where all-cash is unremarkable and should not be treated as signal.

---

## 5. The two vocabulary items — one is a non-issue, one is the real one

### 5.1 PROCEDURE — nothing to build

Ten bills across five months. **Marg already zeroes them itself:**

```
gross      851.15
DR/CR     −850.39
NET          0.00
CASH         0.00
```

They never touch the day total or the cash column. **No subtraction rule is needed.** One less
thing to build, and one less thing to get wrong.

*Noted for the record: `DR/CR` therefore carries two distinct meanings — ordinary round-off
(S180 measured up to ₹19 on a ₹319 bill) and full write-off of a non-charged bill. Anything that
interprets `DR/CR` must expect both.*

### 5.2 HOME MEDICINE — this is the one that breaks the cash reconciliation

**20 bills · ₹24,413 · and Marg records every one of them as FULLY PAID IN CASH.**

| Descriptor | Bills | Net | Cash recorded |
|---|---|---|---|
| `HOME MEDISUN` | 14 | 16,597.00 | 16,597.00 |
| `HOME MEDICINE` | 6 | 7,816.00 | 7,816.00 |

These are billed and never collected at the counter. **How Darpan handles it today (owner, S183):
he deducts the home-medicine cash from his cash in his paper copy, and the NET cash is what carries
forward into the Google Form.** That is why the §4.0 totals still reconcile to 0.3% — his declared
figures already have home-medicine removed. Marg, however, books each home bill as cash, so **Marg's
cash column is overstated by exactly the home-medicine amount** on any day that carries one.

The new system must do that deduction **automatically** — subtract home-medicine bills from the cash
line — rather than leaving it to a paper copy and a man's memory. Left undetected it would manufacture
a shortfall against someone who did nothing wrong, the fastest way to destroy trust in a new system.

**Rules this forces:**

1. Home bills are subtracted from **both** the day total and the cash figure before any
   comparison with the drawer.
2. Detection is a **configurable vocabulary list, never hard-coded** — two spellings already
   exist in five months, and a third will appear.
3. Every excluded bill is **listed on the day's view**. A bill that vanishes silently is worse
   than one that reconciles wrongly, because nobody can see it to argue with it.

### 5.3 Credit notes

**168 bills, −₹56,561** across the five months. Already negative in Marg, already netted, already
stored as a magnitude plus a `_return` service under **D314**. What is owed is a **display
surface** — the owner asked for returns shown distinctly, not merely netted away.

---

## 6. What the Marg export can and cannot tell us

| Question | Marg answers it? |
|---|---|
| What was sold, per bill, per item | **Yes** — 16,118 item lines |
| The day total | **Yes**, and it proves its own arithmetic |
| Cash vs non-cash | **Yes** — the `CASH` column |
| UPI vs card *within* non-cash | **No** |
| Which bills were never collected | **Only** via the home-medicine vocabulary |
| Who billed it (operator) | **Not yet** — requested from the Marg engineer |

**The `.CASH`/`.UPI` mode field remains worthless** and must never be used — S180 proved 23 of 23
bills labelled `.CASH` on a day that was ~30% UPI. It is a ledger label, not a tender. The rule
stands: cash is the `CASH` column, non-cash is `NET − CASH`.

**So Darpan's remaining job is small and honest:** split the non-cash into UPI and card, declare
his drawer, and post expenses and advances. Everything else arrives already proven.

---

## 7. File format — a correction worth recording

Six of the eight exports are genuine Excel-2007 `.xlsx`; `marg_report.py` reads via `xlrd 2.x`,
which handles legacy `.xls` only. The first conclusion drawn was that an Excel round-trip had
destroyed the patient identity in four files.

**That was wrong.** Two of the six `.xlsx` files carry identity perfectly (69% and 85%) — exactly
consistent with their dates being after 19 June. The missing identity in the other four is the
practice change of §4.1, not a conversion artefact. The Excel round-trip damaged nothing.

> **The lesson, and it nearly cost a wrong recommendation:** the arithmetic self-checks passed on
> every file, and that was read as "the data is sound." The self-checks validate the **money
> columns** and say nothing whatever about the **description column**. A green light is only
> green about the thing it checked. Kin of F-95 and one level up from F-88.

**Consequence:** re-exporting those six as `.XLS` would fix the format and recover no identity,
because the phone numbers were never captured. Teaching the parser to read `.xlsx` as a second
reader is therefore the better path — and it also protects the daily feed, since anyone opening
a file in Excel to check it will save it back as `.xlsx`.

---

## 8. What exists, and what must be built

**Already live and verified on the box at S183:**
`marg_report.py` · `finance_ingest.py` · `finance_returns.py` + `finance_returns.sql` ·
`finance_identity.py` · `finance_upi.py` (ICICI arbitration) · `finance_app.py` · the
computed opening/closing views (D313) · two-stage maker/checker approval (D318, clinic module).

**Build status:**

| # | Item | Status |
|---|---|---|
| B1 | `.xlsx` reader in `marg_report.py` | **BUILT + PROVEN offline (S183).** New md5 `829f4344df6e086510bb0fb6112ecb77`. `.xls` path byte-for-byte unchanged (Regression 1); `.xlsx` faithful to a round-tripped `.xls` (Regression 2); selftest 38/38; all 8 files parse. In kit **S183_M2a**. |
| B2 | `marg_export` column map + activation | **BUILT + PROVEN (S183).** `finance_migration_S183_marg_map.sql` — 7 rows (**not** 8: `phone_last4` is barred by the `our_field` CHECK), transforms NULL, `active=1`, marker in `setting`. Additive, atomic, reversible. In kit S183_M2a. |
| B3 | `marg_backfill.py` v2 | **BUILT + PROVEN (S183).** `keep_items=True`, both stores per day, clears `sale_line_item` by `day_entry_id` so both halves supersede identically, ties lines to the bill batch, aborts on row anomaly. Money-untouched + idempotent verified on real April + July data; a false-abort on Marg's zero-net procedure write-offs was caught by the offline test and fixed (expect = non-zero bills). In kit S183_M2a. |
| B4 | Home-medicine vocabulary + exclusion | **TO BUILD** — configurable list; deduct from the cash line; excluded bills always displayed (§5.2). |
| B5 | Watcher on the export folder | **TO BUILD** — hash-based (no naming discipline needed); token-gated PC→VPS push; tells the operator *accepted / refused* at the machine. Also the backfill's file-transport path. |
| B6 | Medical expenses + advances | **TO BUILD** — Darpan posts, owner approves (D318 shape). |
| B7 | Cash-position view | **TO BUILD** — opening → collected → expenses → advances → deposits → closing, one screen. |
| B8 | Bank-visit trigger | **TO BUILD** — lights up for both Darpan and the owner. |
| B9 | Returns display | **TO BUILD** — distinct, not netted away. |

**S183_M2a install status:** kit built, proven offline (installer rehearsed; F-97 currency
gate refuses a wrong live `marg_report.py`; honest red restores), staged to the repo. Install =
`bash /root/deploy/vps_deploy.sh S183_M2a`. The backfill RUN over the 8 files is owner-driven
after install (files are PHI → PC→VPS directly, never git). On install the Register's
`marg_report.py` pin must move `28b47d44…` → `829f4344…` (owed at close-out, like the S183 nine).

---

## 9. Open questions

1. ~~What changed on 21 April 2026?~~ **ANSWERED at S183 (§4.0/§4.2):** a Marg UPI-recording gap,
   not a real event. Darpan declared ₹84,613 of UPI in the window. No action beyond awareness.
2. ~~Was there ever a genuine cash-only period?~~ **ANSWERED: no.** The cross-check settled it.
3. **Marg operator column** — still with the Marg engineer. Until it exists, "who billed it"
   cannot be answered, and the reserve-person-vs-Darpan comparison in the S180 sheet stays parked.
4. **Opening stock register → orthotic inventory → reordering → purchase management** (owner's
   S183 idea). Coherent and worth doing, but it is a **new subsystem touching the asset app**, not
   an extension of this feed. Recorded here so it is not lost; to be scoped on its own once the
   daily feed has run for a week.

---

*S183 · design and evidence only · next free: D322 · F-103 · Session 184*
