# DELIVERY NOTE — kit `S182_C1a` · Clinic daily entry (C1 slice 1)

**Session 182 · contract `S181_Clinic_Module_Build_Contract_C1` + addendum.**
Built offline against the hash-verified copy of the live build
(`finance_app.py` md5 `7b62b7ae661914505c864d71cc6c9abc`). Nothing live was touched.

---

## The differential smoke gate (F-87)

| Run | Result | Failures |
|---|---|---|
| **Baseline** — live build, seeded synthetic db | **167 / 177** | the 10 known seeding artefacts (list below) |
| Live build, seeded db **after** the S182 migration | **167 / 177** | the same 10 — the migration alone changes no behaviour |
| **This build**, migrated db | **227 / 237** | **the same 10 — ZERO new** |

**+60 new checks, all passing.** Both failure lists, identical on every run:
`whoami role · maker tile is not called Finance · maker tile points at the entry
screen · root lands maker on the entry screen · maker cannot cutover · cutover
leaves legacy breaks open · maker cannot post statements · wrong/unset cron
token refused · clearing the full parked amount settles the month · a maker
cannot allocate deposits`
(These are artefacts of the synthetic seed db. On the real store the whole
suite must be green, and `install_c1a.sh` uses the exit code as its gate.
Note: the working brief recorded the baseline as 166/176; the artefact
actually runs 167/177 here because several checks are conditional on data —
the failure LIST is the law, and it matches exactly.)

Also verified: `python3 -m py_compile` clean on every `.py`; every one of the
22 new clinic routes exercised through the Flask test client on its actual
path (F-63), 26/26 assertions green, including the F-79 absence check — the
served entry page contains all six money fields and **no** opening-cash input
element; `finance.db` comes out of the smoke suite byte-identical (it runs on
a throwaway copy, as before).

## What is in this slice

- **`/finance/clinic/…` namespace** on the same app and port. The fail-closed
  gate now resolves the unit from the path: clinic paths demand a `clinic`
  role from `unit_role`, everything else stays the medical surface. A login
  valid on one unit gets a 403 on the other (proven both directions).
- **Maker entry screen** `finance_ui/finance_entry_clinic.html` — Hindi-first,
  phone-first, same style system as medical (inline SVG only, no CDN). Date
  picker only (server refuses future dates); opening cash is a read-only
  display computed by the views (D313) — any `opening` key a client posts is
  never read, proven by smoke; **six money fields** (OPD/X-Ray/Procedure ×
  cash/UPI) stored as `day_line` rows, integer paise; **stray repeater**
  (amount + stream + tender + required reason) stored as `day_line` rows
  tagged `line_kind='stray'` with the reason in `note`; **two evidence
  uploads** (OPD register page · X-Ray+Procedure register page) through the
  SAME scanner-widget/attachment mechanism medical uses.
- **⚠ Additive arithmetic.** Clinic day = sum of all six cells + strays.
  There is no "total" input, so medical's *total-includes-UPI* convention has
  nothing to leak into; a dedicated smoke check (`clinic cash is the cash
  cells alone`) fails the moment medical's formula is applied to a clinic day.
- **Checker view**: the existing review screen hard-codes its API base, so
  `/finance/clinic/review` serves the SAME `finance_review.html` from disk
  with only the API base and the two visible unit names rewritten at serve
  time — the file itself is untouched. Approve (incl. UPI-mismatch
  acknowledgment), corrections, exceptions and the day/month/tile reads all
  work against clinic data via mirrored clinic API routes.
- **Tile wording as settings**: `clinic.tile.maker_title` = "Daily Collection"
  etc., the medical `tile.maker_title` pattern, unit-prefixed.
- **Migration `finance_migration_S182_clinic.sql`** (marker-gated, rollback at
  foot): two nullable `day_line` columns (`line_kind`, `note`); the
  `attachment` table rebuilt to admit the two clinic doc types (see
  "surprises"); clinic tile settings; defensive re-seeds of the clinic unit
  and roster.

## NOT in this slice (deliberately)

- Card / wallet entry fields — they arrive via attribution later; the tender
  vocabulary is one tuple (`CLINIC_TENDERS`) so adding them is not surgery.
- The attribution / shadow-poster checker panel (tracker ingest is C2).
- Clinic month close, cutover, statements, deposit allocation — the clinic
  endpoints exist and answer **501 `not_in_slice`** loudly so the shared
  review screen's buttons never dangle into a 404.
- Clinic expenses / cash movements / non-cash bills; salary advances.
- No medical code path changed except the unit-aware gate; medical proven
  byte-identical in behaviour (ledger snapshot equal before/after a full
  clinic day cycle inside the suite).

## Surprises / contradictions found (reported, not papered over)

1. **`attachment.doc_type` has a CHECK list** that SQLite cannot extend in
   place. S180 refused a table rebuild for `sale_item` because a view could
   carry that change; for a CHECK there is no view-level alternative, and the
   contract forbids a parallel evidence table. So this migration rebuilds
   `attachment` (create→copy→drop→rename, ids preserved, FK-checked, service
   stopped). This is the one non-additive step in the kit; the db is backed
   up first and auto-restored on red.
2. **The review screen has no reject button/endpoint** — in this system
   "reject" is the correction path (a re-submit supersedes; revisions are
   kept verbatim). The clinic checker inherits exactly that, per the code's
   own convention, rather than inventing a new reject flow.
3. **The brief's baseline figure (166/176)** differs from the artefact's
   actual run (167/177) — same 10 failures; conditional checks make the
   totals data-dependent.
4. Medical's approved-day guard compares the broker role string; the clinic
   route uses the resolved per-unit roles for the same guard (fail-closed
   either way; noted for consistency review later).

## Kit contents

| File | md5 |
|---|---|
| `finance_app.py.new` | `5282eba729226faee5c276e9f74927e7` |
| `finance_ui/finance_entry_clinic.html.new` | `854a8cd0f7d05f717d92da1c3d626364` |
| `finance_migration_S182_clinic.sql` | `e0262d157c1b7c979531a8f53378c31d` |
| `KIT_ID.txt` | `8e178a62bb779aeb42ff0087898cc150` |
| `install_c1a.sh` | `50023c23148ee9c26e4998f1838bf60e` |

`KIT_ID.txt` (F-88): `S182_C1a 5282eba729226faee5c276e9f74927e7` — the
installer refuses to run if `finance_app.py.new` does not hash to the id line.

## Install

Upload the kit into `/root/finance` (keeping `finance_ui/` nesting), then run
`bash install_c1a.sh`. One &&-chained block: md5 gate → kit identity → service
stop → app+db backup → swap → py_compile → migration (skipped when its marker
row exists) → smoke as gate → restart only on green → automatic restore of app
AND db from the `.bak_S182` copies on red.

Post-install, same class of steps as S179: confirm the clinic roster's real
SSO usernames (`SELECT * FROM unit_role WHERE unit='clinic'` — a role keyed to
a wrong username grants nothing, silently), and put the clinic tile on the
portal pointing at `/finance/clinic/` (tile text comes from
`/finance/clinic/api/tile-meta`).

---
## C1b addendum (supersedes C1a — F-88 new-name rule)
C1a's installer assumed the retired WinSCP delivery (`cd /root/finance`) and refused when run
from the repo kit directory: the md5 gate fired FIRST, before the service stop — **the live
system was never touched** (owner-verifiable: live finance_app.py still `7b62b7ae…`). Its red
branch also printed "restored" over no-op copies. Both fixed in `install_c1b.sh`: stages from
the kit dir itself; red branch reports whether live files were actually touched (marker-file
guard). Payload is byte-identical to C1a — same md5s. Kit name and KIT_ID advanced per F-88.
RULE (candidate): an installer is gated end-to-end through its ACTUAL invocation path before
shipping — F-63's route-must-be-exercised lesson, applied to installers.
