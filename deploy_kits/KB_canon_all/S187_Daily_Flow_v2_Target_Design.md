# S187 — Daily Flow v2: Target Design (owner directive, 18 Aug 2026)

**Status: DESIGN — nothing here is built. Becomes a build contract on the owner's sign-off,
then ships as staged gated kits (the S181 C1 pattern). Three decisions are the owner's and
are listed in §9.**

**Owner's directive, verbatim intent:** ICICI daily UPI auto-retrieved from clinic email ·
Yes Bank statement ingest · Darpan lands from the Sanjeevni tile, scans his register pages in
the inbuilt scanner, makes his entries, saves, THEN sees the aggregated bank-UPI and Marg
results, and files · the owner's page lists missing Marg exports, shows Darpan's filed page
for approval, expands to bill-level detail and that day's bank data, files as approved ·
salary entries editable with month + instalment logic from attendance, narrations on salary
and other expenses · home and procedure medicine bills visible, expandable to item level ·
plus every other friction-reducing, full-visibility feature that fits.

---

## 0. What already exists (so nothing live is rebuilt without need)

| Asked for | State |
|---|---|
| ICICI UPI auto-retrieve from clinic email | **LIVE since S179.** `VPS_Push_UPI.gs` pushes the daily MPR at 09:30, dedupe, `{"ok":true,"pushed":8}` verified. Nothing to build — only to SURFACE it per-day on both pages. |
| Yes Bank statement ingest | **LIVE since S186 as manual CSV upload** on the workbench (`finance_yesbank.py`, both-direction reconcile, `deposit_unevidenced` never a pass). §5 adds an email auto-retrieve IF the statement arrives by email (owner to confirm — §9 Q3). |
| Marg export reaching the box | **LIVE since S186/S187**: checker upload on the workbench + the B5 pushed path (reception sender, staged, checker applies). |
| Darpan's tile → entry page → scanner → entries → save | **LIVE since S179/S181** (Daily Sale, per-document scanner pages, four-tender entry). |
| Approve flow | **LIVE** (submit → checker approve; UPI mismatch requires acknowledge). |
| Bill-level and item-level data | **IN THE STORE** since the S183 backfill (`sale_item`, `sale_line_item`, 15,574 lines) — but not surfaced expandably. |

The build is therefore mostly **surfaces and one bridge**, not new pipelines. The one genuinely
new integration is salary ↔ Staff Ledger (§4), and it is **gated on a verification** (§4a).

## 1. The spine: ONE canonical Day Page (`/finance/day/<date>`)

Every surface — Darpan's entry, the owner's approval queue, the workbench, the dashboard, any
flag or exception — links to the same expandable day view instead of each screen re-inventing a
partial one. **Same data, same level, everywhere; role decides scope, not the page.**

Sections, each a collapsed card that expands in place:

- **Declared** — Darpan's tenders (cash/UPI/card), strays, drawer expenses w/ narrations, scans (thumbnails inline, click → full scan).
- **Marg** — day total, bill count, variance-vs-declared chip (green ≤ ₹2,000, the S183 measured threshold; red above → **expand to bills** (bill no, patient, mode, net) → **each bill expands to drug lines** (item, qty, batch, expiry, amount). Credit notes shown distinctly, never netted away (B9).
- **Bank · ICICI** — that day's settled UPI rows from the MPR; matched / mismatch state; ack trail.
- **Bank · Yes Bank** — deposits touching that day; `evidenced / unevidenced` state carried visibly.
- **Home + procedure medicine** — the B4 vocabulary (configurable list) deducts from the collectable line and the excluded bills are ALWAYS displayed, expandable to items (§6).
- **Flags & exceptions** — every `data_flag`, `line_sum_vs_day_total`, review count for the day, expandable to rows.
- **Custody** — the day's custody events (taken/carried), once the Hindi labels unblock the entry-side block.
- **Audit** — who entered, edited, verified, approved, when. Visible, not buried.

## 2. Darpan's flow v2 (maker) — save first, see after, file with eyes open

Tile → his page → scan register pages → enter tenders/expenses → **Save** → the **Day Mirror**
appears → **File day**.

The Day Mirror (new): after save, his own numbers beside the machine's — declared UPI vs
bank-settled UPI (match / gap), declared total vs Marg total (variance chip), missing-scan
nudge, unfiled-yesterday nudge. In plain Hindi-first labels (blocked on the label sign-off, as
before; English until then).

**The independence question, decided by design:** the S183 cross-check is only meaningful
because Darpan's declaration and Marg are independent records. His own sequencing ("save,
then see") preserves that — but an edit after the reveal would quietly destroy it. Options in
§9 Q1: hard-lock tenders at first save, or allow edits but stamp them `edited_after_reveal`
so the checker sees a badge. **Recommended: the stamp, not the lock** — the app enforcing
correctness should be a feature, not an obstacle (F-105), and a lock forces round-trips for
honest typos; the badge keeps the audit honest either way.

Friction cuts on his side: yesterday-carry (opening shown, no re-typing) · one screen, no
tabs · the file button disabled until scans attached OR a stated reason (blank is UNKNOWN,
never zero) · his view of the Day Page scoped to his own day (no month aggregates, no cash
position — medical's checker remains the doctor alone).

## 3. The owner's flow v2 (checker) — one landing, everything expandable

**Landing strip (counts, each click-through):** days awaiting approval · missing Marg exports
(day filed, no Marg batch — plus `MARG_DAY_NOT_FILED` flags, plus pending B5 pushes) · missing
days (D322-aware: Sundays/holidays optional) · UPI mismatches unacknowledged · Yes Bank
unevidenced deposits · review-queue count · variance-over-threshold days.

**The approval queue:** each filed day = one row → expands into the full Day Page (§1) inline →
**Approve** right there. Approve-with-one-edit: fix a narration or recategorise an expense
inline while approving (audit-trailed as the checker's edit) instead of bouncing the day back
to Darpan. Bulk-approve deliberately NOT offered — one day, one look, one click is the design.

**Month view stays** (the existing review KPIs/grid), gaining the same expand-in-place rows.

## 4. The salary bridge (checker-side; the one genuinely new integration)

What the owner asked: edit salary entries, add month, instalment logic from the attendance
section, narrations on these and other expenses.

**Where the truth lives today:** salary/instalment logic is the **Staff Ledger system**
(D258/D259: the instalment IS the whole monthly deduction, ₹1,000 interest out of it,
waterfall across tranches, skip months capitalise; `/salary` is checker-only; a locked month
is never recomputed — corrections are next-month adjustments). Finance holds only drawer-level
`salary_advance` expenses. **Two systems, one rupee — this is exactly where double-counting
lives.**

**Design:** finance does not grow its own salary logic (D202 — one authored source). Instead:
(a) the Day Page's expense section shows, beside each `salary_advance`, the Staff Ledger's
view of that staff member (balance, open tranches, next instalment) read-only via the shared
SSO origin; (b) a **post-to-Ledger** action (checker-only) books the advance into the Ledger
with narration — closing the B6/backlog-6 gap where ₹70,000 of Darpan's advances rest on an
unverified SQL comment; (c) month/instalment **edits happen in the Staff Ledger app**, one
click away, not re-implemented in finance; (d) narrations editable on any expense row,
audit-trailed, both apps.

**§4a — GATE, before any of this is built:** backlog item 6 — read the Staff Ledger from the
box and establish what those ₹70,000 of advances actually look like there TODAY. The record
asserts "tracked in salary system, NOT posted to Ledger" and nobody has looked. Building a
bridge on an unverified claim is F-112's shape. **The check is one read-only session step and
it comes first.**

## 5. Feeds — close the last manual hop

- **ICICI UPI:** live; surface per-day (nothing new server-side).
- **Yes Bank:** IF the statement reaches the clinic email (owner confirms, §9 Q3): a
  `VPS_Push_YesBank.gs` clone of the UPI pusher, same token pattern, same dedupe; the manual
  upload stays as fallback. If it does not: upload stays primary; a monthly nudge chip
  ("statement now 12 days old") keeps it honest — `deposit_unevidenced` already refuses to
  pass silently either way.
- **Marg:** live both paths. Add the missing-export list (§3) so the absence of a push is
  visible the same morning, not at month-end.

## 6. Home + procedure medicine (B4, owed since S183)

A configurable vocabulary marks bills as home-medicine / procedure-medicine. They are
**deducted from the collectable-cash identity** (they are billed, never collected at the
counter) and **always displayed** — their own strip on the Day Page, expandable to items, so
the deduction is inspectable rather than silent. The S183 finding stands: totals already
absorb them within 0.3%, so this is visibility + correctness of the cash identity, not a
money correction.

## 7. Ambient friction-cuts (the "think of all other such features" list)

- **Missing-day WhatsApp nudge** (owed since S179): 21:30, if yesterday unfiled/unapproved — one template message, DRYRUN-gated behind F-82's vendor restore; until then a dashboard chip.
- **Scan thumbnails** inline everywhere a scan is referenced.
- **The four flagged days** (3 May, 9 May, 2 Jun, 12 Jun ₹8,487) surfaced as standing chips until cleared — live money should not live only in a backlog doc.
- **Accountant month-pack** (B7, owed): one click, month `.xlsx` per entity, patient-name toggle default OFF (F-31).
- **Bank-visit trigger** (B8): cash-in-drawer over threshold lights a chip for both Darpan and the owner.
- **Keyboard-free approve:** the queue advances to the next pending day after each approve.
- **Every count on the landing strip is a link** — no number without its rows one click away.
- **Print view** of the Day Page (clean, no chrome) for the physical file.

## 8. Staging (each kit gated, offline-rehearsed, F-87 differential, restore-on-red)

| Kit | Contents | Depends on |
|---|---|---|
| **D1** | The Day Page + the owner's landing strip + approval queue with full expansion (bills → items, both banks, flags, audit) | nothing — data all exists |
| **D2** | Darpan's Day Mirror + save-then-reveal (+ chosen edit policy) + his scoped Day Page | D1 |
| **D3** | Salary bridge: read-only Ledger panel + post-to-Ledger + narration editing | **the §4a box check first**, then owner OK |
| **D4** | B4 home/procedure vocabulary + cash-identity deduction + display | D1 |
| **D5** | Yes Bank GAS pusher (if Q3 = yes) · nudge cron (when F-82 clears) · month-pack (B7) · bank-visit chip (B8) | independent |

D1 is the largest and unlocks everything; D2 changes Darpan's habits and should land only when
the owner is ready to walk him through it once.

## 9. The owner's three decisions

1. **Edit-after-reveal policy (§2):** stamp-and-badge (recommended) or hard-lock at first save?
2. **Salary edits (§4):** bridge-to-Ledger as designed (recommended), or replicate instalment logic inside finance (advised against — two authorities on one rupee)?
3. **Yes Bank by email (§5):** does the statement arrive in the clinic Gmail? If yes, the auto-pusher is a small clone of a proven part.

*Also carried, not decisions: the Hindi labels still gate Darpan-facing wording and the custody
block; the §4a Staff Ledger check precedes D3.*

---
*S187 design · to be contracted before build · Register v5.14 is current · next free D326 · F-125.*
