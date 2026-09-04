# HANDOFF RUNBOOK — S223 close · 04-Sep-2026 · v155

*Supersedes v154 (S222 close). Tier 0.*

---

## §0 · WHAT HAPPENED

**The longest single sitting this project has had: 22:00 IST on 03-Sep to after 07:00 on 04-Sep.**
The owner was awake for almost all of it, through a stomach upset, and said the work was what was
keeping him occupied. He slept from about 22:00 to 01:30 and worked from there.

1. **Phase 0, and the two S222 staged kits installed** — `asset_register.py` `71bd3277…` with
   `/scanapp` live, `portal.py` `d15acef3…`. Repo reset `e4b25f5` → publish → `685e990`.
2. **The S222 canon debt paid in full**, and **F-301 found in the paying**: `KB_Register_v5_69_S221`
   had no S221 wave at all while four self-referential lines said it did. Eleven live truths would
   have been erased by regenerating the pin list from it, exactly as step A8 instructs.
3. **Docterz Revenue Stage 1 built and shipped in one sitting**, on the owner's *"DO NOW"*.
   68 days · 2,179 entries · 206 split legs.
4. **The Day Revenue screen**, shaped message by message by the owner, printed on A4.
5. **The bank reconciliation** — ₹47,530 decomposed; **₹43,330 residue across 27 clean days**,
   consistent with UPI bills rung as cash. **₹18,100 of invisible tender** recovered from 79 raw
   exports.
6. **The register card** — his idea, replacing his own plan for a spreadsheet.
7. **F-303 — the finance app 503 at 04:35, ours.** Rolled back in one paste. Both root causes fixed.
8. **The drawer count**, his design, with **the fourth signal** that came out of his *"just a thought"*.
9. **The X-ray list** built from the clinic's own 6,177-entry register (F-306, F-307).
10. **D367 minted** — the rows are the truth.
11. **Five specifications dictated at dawn. None built. All written down.**

**New fault codes: F-302 … F-307.** New decision: **D367**. Next free **F-308 · D368 · S224**.

**SOP change:** none. **Surveillance scope:** unchanged.

---

## §1 · MENTAL MODELS THAT EARNED THEIR PLACE THIS SESSION

**Every record needs a physical check that does not depend on the person who made the record.**
This arrived by accident — the owner kept asking the same question about different things — and it
is the most durable thing S223 produced.

| | what is written down | what physically checks it |
|---|---|---|
| cash | register + physio | **the drawer count** (live) |
| UPI | register modes | the bank MPR (live) |
| X-ray film | purchases − consumption | **the printer counter** (specified) |
| cast consumables | purchases − consumption | a shelf count (specified) |

**A total handed to you is a claim; a total you derive from the lines is a measurement** (D367).

**A manual column is always abandoned** (F-306). The clinic's own X-ray register proves it twice:
film sizes filled ~515 rows then dropped, `UPLOADTO DOCTERZ` marked OK 549 times then dropped, while
the register itself ran on to 6,177 entries. **Nobody decided to stop.** Either the system already
knows the value, or it is one tap inside a flow the person is already in.

**Anything that will be counted later must be chosen, not typed** (F-307).

**Mounting must touch nothing** (F-303). And when copying a pattern from a working module, read what
it *does*, not what it looks like.

---

## §2 · THE LIVE BACKLOG

**⭐0 — FIRST ACTION AT S224, before any build:**

1. **Capture the DECLARED-PENDING S223 pins from the box** — `tile_grants.json`,
   `finance_clinic_day.py`, `docterz_day.py`, `docterz_ingest.py`, `clinic_upi_check.py`. They are
   kit pins with install output seen and **were never read back**. They are not passes.
2. **Capture the eight PENDING S221 8-char prefixes** — outstanding since S221, carried through
   two closes.
3. **Publish and install the drawer count** — `clinic_register.py` `93a31e68…`, built, 89/89 green,
   committed, **not published and not installed**.

**⭐1 — the dawn specifications, in the owner's own build order:**

1. Two scoped PWA logins — Manoj Bhati (physio revenue view only) and **Awdhesh** (X-ray + procedures).
2. The physio revenue view (smallest; `clinic_physio_day` already exists).
3. Awdhesh's pre-listed X-ray film screen, with backlog.
4. Procedures, with contextual consumables and an add-anything fallback.
5. Printer counter + stock arithmetic + refill reminder with its recheck.
6. The X-ray image worklist and its three checks.
7. Moving the Docterz capture to the reception PC (medical-PC pattern: Claude Desktop for discovery,
   then a script over Tailscale).

**⭐2 — owed technical work:**

- **The tracker-side parser fix** — proven offline, **not installed**. Until it lands, tomorrow's
  splits need `push_day_tenders.py` re-run.
- **Reconcile the new Docterz reader against `S211_DAYREVENUE`'s 67-workbook rehearsal.** The new one
  was tested on eight.
- **The nine split-gap days** awaiting raw exports: 27-Jun · 04-Jul · 08-Jul · 13-Jul · 14-Jul ·
  15-Jul · 18-Jul · **05-Aug (₹3,700 unresolved)** · 27-Aug.

**⭐3 — rulings owed by the owner (some very old):**

- **`darpan_app.py` divergent copies — awaiting his ruling since the S210 close, now load-bearing.**
  Three divergent full copies, fourteen patchers, none reproducing the live `c98f0c24…`, which is why
  the S222 corrections fix had to be a page-level hide rather than a source fix.
- S214 / S215 / S216 candidate sets — recorded, not minted.
- The four Docterz candidates in §7 of the working paper.
- **Five one-word answers on the procedures draft** — HBK · POP · undercast padding · the draft
  quantities · ILI consumables.

**Parked by the owner:** the advances build (*"park it"*); the spot-count anchor.

---

## §3 · INSTALL DISCIPLINE — what S223 changed

- **A gated installer must be the only thing that writes its payload** (F-302). If a paste also
  copies the file, the gate is answered before it is asked and takes no backup.
- **Every install line now checks `systemctl is-active` after the restart and restores its own
  backup if the service does not return**, printing the log. Adopted after F-303 left the owner at a
  503 with a manual rollback.
- **`init()` mounts. It does not open a database.** Schema on first request.
- **A test fixture must be harder than production, never easier** (F-303/F-286). The register test
  now uses a getter that raises outside an application context.
- **Slice-based edits assert their own bounds** (F-304).
- The VPS was unreachable to the assistant all session; **every install was a single owner paste.**

---

## §4 · THE BOUNDARY

- **The publish is the owner's double-click**: `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`
- **Patient data is not in this project. No patient number in the repository (F-185).**
- Owner's ruling for the revenue screens: **clinic ID and NAME on the view, no mobile number.**
- Nothing live is rebuilt without his explicit OK; the manual workflow stays as fallback.
- **ClickUp is parked (D17).**

---
*v155 · S223 close · 04-Sep-2026. Written before the manifest, as the routine requires.*
