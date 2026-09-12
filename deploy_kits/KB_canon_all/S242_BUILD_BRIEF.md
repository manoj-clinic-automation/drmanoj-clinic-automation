# S242 BUILD BRIEF — the staff app stopped being a prediction

*12-Sep-2026. One brief instead of ten papers: the shortest complete path into what S242 did.*

## The session in one line

Three portal changes in an evening — and within the hour, two members of staff used them and the
daily register carried its first entry ever.

## The three changes

| # | what | files | pins |
|---|---|---|---|
| **D481** | `Docterz daily collection` granted to Shavez, Shivani, Alisha | `tile_grants.json` | v10 `812cbbc6…` → v11 `710f13bd…` |
| **D482** (F-444) | the register opens on **today** | `clinic_register.py` | `93a31e68…` → `c6b87682…` |
| **D483** (F-445) | Amir gets one tile — his own page | `portal.py` + `tile_grants.json` | `ed558b36…` → `d08721f6…`; v11 → v12 `7e7445a3…` |

Kits, all in `D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\`:
`S242_DOCTERZ_COLLECTION_TILE` · `S242_REGISTER_TODAY` · `S242_AMIR_TILE`.

## The three things worth knowing next time

**1 · The repository can rebuild `portal.py`, and did.** It holds no full copy — one S204 base
(`24ea2c0b…`) and a chain of anchored patchers. Replaying them reproduces **every declared pin
exactly**, landing on `ed558b36…`, the pin the S239 kit declares live. That is how a kit gated on a
hash without anyone reading one off the box. The chain is written out in
`deploy_kits/S242_AMIR_TILE/EVIDENCE_portal_reconstruction_S242.txt`.

**2 · `clinic_register.py`'s live bytes ARE in the repository** — at
`deploy_kits/S223_REGISTER_CARD/clinic_register.py`, hashing to `93a31e68…`, the drawer-count build
read back from the box on 04-Sep and unmoved since. Confirmed three ways in one turn before it was
trusted: the Register's live table, `live_pins_S224close_READBACK`, and the file's own text matching
what the live page renders.

**3 · Walk the real thing.** The register walk mounted the patched module on a real Flask app over a
real sqlite database shaped like the live one. The tile walk imported `portal.py` and asked its own
`_visible_sections` what each person is shown — not what the JSON says. Both then re-ran on the box
before anything was copied, and the Amir installer was additionally rehearsed end to end.

## The two rulings that change how future sessions read a screen

**D484 — the drawer count is optional by design.** The nine boxes are the record; they reconcile
against the overnight Docterz report and the bank MPR without a note being counted. The
notes-and-coins count is a convenience, offered and never demanded. **A day with the boxes filled
and that section blank is COMPLETE and is never to be flagged.**

**F-446 / F-447 / F-448 — the session's three self-findings, and they rhyme.** An empty drawer
section was reported as a missed step when it was a design; a dead device shell had been allowed to
block three close steps of which **only one ever needed a shell**; and the consequence was concrete —
the folder's own Phase-0 gate had been **exiting 1 since the S241 close** with three canon files in
no row at all, and nobody had run it. `gen_live_pins.py` and `MD5SUMS_ALL.txt` both ran in the
workspace at this close (pin list verified, gate rebuilt 485 → 495 rows, added 10, dropped 0, exit 0),
clearing a debt carried since S238.

> **An empty field is a question, not a verdict. When a step is blocked, name the resource it needs,
> not the tool that failed.**

## What is live and quiet

`amir_claim` has **no rows**. Amir's day on 12-Sep was OPEN with neither purchase report arrived,
136 bills carried, and the salt list unticked — he starts on the page tomorrow. **Darpan's claim
queue is the next build, and it opens on an empty table by design.**

---
*`S242_BUILD_BRIEF` — project knowledge · `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S242\` · loose on the SSD.*
