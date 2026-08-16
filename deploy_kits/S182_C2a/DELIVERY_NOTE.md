# DELIVERY NOTE — kit `S182_C2` · Clinic entry redesign (owner-directed)

**Session 182 · slice C2.** Built offline on top of the hash-verified LIVE build
(`finance_app.py` md5 `db5980a1aa80d6778a62d264bfef0822`, the C1e kit). Nothing
live was touched. The C1e migration is assumed APPLIED on live (it is); this
kit's own migration is separate and marker-gated (`migration.S182_c2`).

---

## The differential smoke gate (F-87)

| Run | Result | Failures |
|---|---|---|
| **Baseline** — C1e build, seeded db + C1e migration | **228 / 238** | the 10 known seeding artefacts |
| C1e build, seeded db + C1e migration **+ C2 migration** | **228 / 238** | the same 10 — the migration alone changes no behaviour |
| **This build**, both migrations | **304 / 314** | **the same 10 — ZERO new** |

**+76 new checks, all passing.** The identical failure list, every run:
`whoami role · maker tile is not called Finance · maker tile points at the entry
screen · root lands maker on the entry screen · maker cannot cutover · cutover
leaves legacy breaks open · maker cannot post statements · wrong/unset cron
token refused · clearing the full parked amount settles the month · a maker
cannot allocate deposits`
(Synthetic-seed artefacts; on the real store the whole suite must be green and
the installer uses the exit code as its gate.)

Also verified: `python3 -m py_compile` clean on every `.py`; every new/changed
route exercised through the Flask test client on its actual path (F-63),
including a standalone probe pass outside the suite; the two F-79 absence
proofs (below); `finance.db` byte-identical before/after the suite (md5-checked
— it runs on a throwaway copy); the C2 migration run TWICE is a no-op;
`PRAGMA foreign_key_check` clean. The smoke's "must stay last" S180 block is
still last; all C2 checks sit above it.

### F-79 absence proofs (the two demanded)
1. The served entry page contains **none** of the six retired cell ids
   (`opd_cash opd_upi xray_cash xray_upi proc_cash proc_upi`) — six explicit
   absence checks, plus four presence checks for the new fields.
2. The string **`सबूत` appears nowhere** on the served entry page ("remove दो
   सबूत word"); the card is now "Register pages — attach both".
Bonus absence: the MEDICAL review screen, read from the same file on disk,
carries none of the injected C2 layer (checked: no `c2VerifyLayer`, no
`skip_verification`).

---

## What is in this slice

- **Four tender totals replace the six cells** (owner): Total Cash · Total UPI ·
  Debit Card · Razorpay ("online booking payments through Docterz"). Stored as
  `day_line` rows (`service='collection'`, `line_kind='tender'`) — except
  **razorpay**, which `day_line`'s mode CHECK (`cash/upi/card/credit`) refuses;
  it rides the new additive side table **`clinic_line_side`** (NO table rebuilt
  — hard constraint honoured). The clinic day/month/day-list/tile reads join
  the side rail back in, so revenue is always whole. **Compat:** the old
  six-cell payload keys are still accepted and stored exactly as C1 stored
  them (proven by the untouched C1 row-count checks and a dedicated compat
  check); the new UI sends only the four.
- **UPI reconcile untouched and proven safe:** `reconcile_upi` sums
  `mode='upi'` `day_line` rows only. Dedicated checks show a day with card 350
  + razorpay 450 + UPI 800 reconciles as **entered 800** — a card amount can
  NOT enter the bank comparison, structurally.
- **Extras simplified** (owner): amount + tender (cash/UPI/card/Razorpay) +
  required narration ("What is this amount?", ≥3 chars). No stream dropdown;
  an old-shape stray's stream is accepted-and-ignored (kept as service when
  valid, for history).
- **Expenses** (owner: "expenses field is missing"): repeater (amount + required
  "What was it for?" note) → `day_expense` rows, so the shared views already
  subtract them from the drawer. Grand Total of Cash = opening + cash
  (incl. cash extras) − expenses; negative drawer refused server-side.
  Card/UPI/Razorpay never touch the drawer.
- **Two-stage approval** (owner: "shavez can be a middle approver, me being
  final checker"): new `clinic_verification` side table + POST
  `/finance/clinic/api/verify/<date>`. Any clinic checker verifies a
  *submitted* day — except the person who entered it (**self-verify → 403,
  plain English**, D272). `clinic.final_checker` (= `manoj`) is a **setting,
  not code**; every other checker (bhawna included — she can verify) gets 403
  `not_final_checker` on approve. The final checker is never hard-blocked: an
  unverified day approves with explicit `skip_verification: true`, recorded in
  the approval audit as **"approved without middle verification"**. A
  correction CLEARS a stale verification (warned). The UPI-mismatch
  acknowledge gate still sits behind all of it, behaviour unchanged.
  `shavez` gains `('clinic','shavez','checker')` via the migration; his maker
  row stays. "verified" is deliberately NOT a `day_entry.status` value — that
  CHECK cannot be extended without a rebuild; verification is a side-table
  fact over `status='submitted'`.
- **Entry UI rebuilt in simple English** (`finance_entry_clinic.html`): title
  "Clinic Entry Form"; Opening Cash with the owner's exact hint ("पिछले भरे
  दिन से चली आ रही नक़दी — comes automatically, cannot be edited anywhere");
  the four money fields; Extra Collection and Expenses repeaters; Grand Total
  of Cash panel + Day Total line; the Docterz/Tracker card; the two scan boxes
  + missing-scan reason. Same visual system, inline SVG only, no CDN, numeric
  keypads, live totals, shout box, deposit warning, confirm_large flow all
  kept. Small Hindi helper lines only where they genuinely help.
- **Review screen, medical file untouched:** the C2 layer is injected at serve
  time into `/finance/clinic/review` only (same rule as the C1 API-base
  rewrite). Non-final checkers' button reads "Verify this day" and posts the
  verify route; the final checker sees "Verified by shavez at HH:MM" / "Not
  verified yet" and the skip-confirm flow; a "Docterz / Tracker — day revenue"
  line renders per day.
- **Tracker feed** (owner: "all get to see the staff output sheet revenue
  data"): new additive `tracker_day` table; POST `/finance/api/tracker-feed`
  gated EXACTLY like `/finance/api/upi-statement` (X-Finance-Cron token, or a
  signed-in checker by hand); payload stored verbatim, upserted one row per
  (unit, day); junk refused loudly (bad date/unit/shape 400) and **privacy
  enforced at the door** — a line carrying name/patient/phone/mobile/contact
  keys is refused whole, and line keys are whitelisted to
  `clinic_id · source · net`. GET `/finance/clinic/api/tracker-day/<date>` is
  visible to clinic makers AND checkers (all three levels), "not received yet"
  when absent. Read-only attribution context (D313: the spine reads, never
  posts).
- **`gas/VPS_Push_TrackerDay.gs`** — Apps Script for the clinic Gmail account
  in the VPS_Push_UPI style: Script Properties for token+URL (no secrets in
  the file), daily trigger ~21:30, finds the Drive-synced
  `revenue_ledger.csv` by filename, filters the day's rows, builds the payload
  above, posts with the cron header, dedupes via a per-day payload-hash
  Script Property, mails on failure only. Sends clinic ids (digits only) +
  amounts — no names, no phones, so nothing needs masking.
- **Migration `finance_migration_S182_c2.sql`** — idempotent, marker
  `migration.S182_c2`, rollback (plain drops — nothing rebuilt) at the foot.
  Also updates the maker tile *subtitle* (it named the retired six-cell
  scheme); the title "Daily Collection" is untouched.

## Adjusted clinic checks (each one a contract this slice deliberately changed)

1. The six `clinic entry has the <cell> field` presence checks → four
   new-field presence checks **plus six F-79 absence checks** on the retired
   ids (the owner removed the cells).
2. `clinic entry is Hindi-first` → `clinic entry keeps the owner's Hindi
   opening-cash hint` (the page is now simple English by direction; the one
   Hindi line the owner specified is asserted verbatim).
3. `clinic entry has the stray repeater` → relabelled `extra-collection
   repeater` (same `addStray` id asserted).
4. `a stray with an unknown stream is refused` → `a stray with an unknown
   TENDER is refused` (the stream dropdown is gone; stream is now
   accepted-and-ignored, tender is what validates).
5. `clinic approve refuses over the open UPI mismatch` → same assertion, now
   preceded by the new verify step (the two-stage gate sits IN FRONT of the
   UPI gate, so the sequence gained: bhawna-cannot-final-approve → 409
   `not_verified` → maker-cannot-verify → shavez verifies → second verify says
   already → day API shows verification → then the ORIGINAL upi_mismatch 409
   and acknowledge-200 pair, both unchanged).
   Every other C1 check is verbatim and passing.

## Schema CHECKs routed around (inspected first, none rebuilt)

- `day_line.mode IN ('cash','upi','card','credit')` — no `razorpay` → side
  table `clinic_line_side`. (`card` IS legal, so only razorpay rides the side
  rail.)
- `day_entry.status` CHECK — no "verified" state added; verification is a side
  table over `submitted`.
- `unit_role.role` CHECK — no new role value needed; the middle approver is a
  plain `checker` + the `clinic.final_checker` setting.

## NOT in this slice (deliberately)

- **Portal tiles are NOT** (owner does those; tile text still comes from
  `/finance/clinic/api/tile-meta`).
- Installer / KIT_ID / SUMS — shipped by the owner per protocol.
- Clinic month close, cutover, statements, deposit allocation — still 501
  `not_in_slice`, unchanged.
- Any medical route/UI change beyond zero (medical proven ledger-identical
  before/after the whole clinic cycle inside the suite; the medical review
  page proven free of the injected layer).
- Wiring the GAS pusher (needs the clinic account's Script Properties and the
  live `revenue_ledger.csv` header names — the parser fails loudly + mails if
  a heading is missing, rather than guessing).

## Kit contents

| File | md5 |
|---|---|
| `finance_app.py.new` | `86382f62907b65cf17fded2ee914328e` |
| `finance_ui/finance_entry_clinic.html.new` | `0c64fda2005ea3cd6692aeb8fd3dc728` |
| `finance_migration_S182_c2.sql` | `22c67f25b17e39faaaf66376df10c373` |
| `gas/VPS_Push_TrackerDay.gs` | `4e5c5b97d945fb63f8807bef54251be1` |

Base build hashes this kit was built ON TOP of (verify before install):
live `finance_app.py` = `db5980a1aa80d6778a62d264bfef0822`.

## Notes for the installer (owner-authored, not shipped here)

- Apply order: swap app+UI → run `finance_migration_S182_c2.sql` **via the
  venv python** (`/root/wa/venv/bin/python3`, `sqlite3.executescript` — the
  sqlite3 CLI is absent on the VPS, C1b lesson) when `migration.S182_c2` is
  absent → `--selftest` as the gate.
- The smoke's three C2 test days sit BEFORE the earliest clinic entry in
  whatever store it runs on, so they can never collide with a real approved
  day (the C1d live-shaped-store lesson, applied at design time).
- Post-install reads worth doing once: `SELECT * FROM unit_role WHERE
  unit='clinic'` (shavez should show maker AND checker), `SELECT value FROM
  setting WHERE key='clinic.final_checker'` (= manoj).
