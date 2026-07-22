# HANDOFF RUNBOOK — 22 Jul 2026 · Session 150 · v88

**Dr. Manoj Agarwal Clinic automation · Bareilly.** Tier 0 (session loop). Supersedes v87 (S149).
Read with `CANONICAL_MANIFEST.md` + `KB_Register` (v2.3) at the start of Session 151.

---

## §0 — What happened in S150 (FULL EOS — one Tier-2 frozen product changed under waiver)

A build session on the **frozen** Nutrition/Diet write-path (`clinic_writer`, Tier 2, D247). The owner
asked for a batch of doctor-approved changes; the product was **unfrozen under an explicit waiver
(D248, D34 discipline)**, changed, verified, installed, and **re-frozen** with a version bump. **No
VPS/live code was touched. No live patient data was opened.**

- **Base verified first** — the 5 `clinic_writer` code files md5-matched the dossier before any edit
  (D172/D188). All work confined to **`vitals_page.html`** (v26 → **v28**). Engine, Flask app and the
  20/14-col ledger schemas untouched; archived-PDF/print output **byte-identical**.
- **Changes:** (a) Hindi spelling/grammar tidy in the LIB strings — **closes the dossier's sole open
  caveat**; (b) exercise library **126 → 128** (Frozen-Shoulder Internal-Rotation towel; Rotator-Cuff
  Cross-Body) + a PIVD knee-to-chest **stop-rule** + a bottle-roll **dose** fix; (c) the Excel
  `Diet_Chart` tab **ported** as a new optional printable **diet-aware** diet sheet ("Include diet
  chart" checkbox, default ON; **no shopping list**; sections A/B/C + comorbidity D), fed to the
  existing text-only archive seam with **zero engine change**; (d) a **screen-only** reading-comfort
  `@media screen` theme (**print fully isolated + byte-identical**). Late owner label tweaks:
  "घर की एक्सर्साइज़"; diet-sheet heading "दैनिक भोजन".
- **A build-time `ReferenceError`** (Section-B `cond` used a `planBlocks`-only variable) was caught by
  the **functional node smoke test** before delivery and fixed — `node --check` passed the syntax but
  not the scope. **Not a fault; no F minted.** Lesson: the artefact-level second check is mandatory.
- **Installed:** `vitals_page.html` **v28, md5 `fcedae303b620f3e5199f4b1e4766510`** — owner-confirmed live on
  `D:\clinic_writer\` (saved under the original name, old file deleted, runs via `open_vitals.bat`).
- **Docs:** Nutrition dossier → **v1.1**; Register → **v2.3** (D248 indexed); Archive **§S150 appended
  → v1.2**; manifest updated last. **D248 minted; F-46 free.**

---

## §1 — Mental models (unchanged, load these)

- **Three-product lineage (D246):** Followup Tracker (clinic PC, offline — SOURCE) → Callback Tracker
  (VPS, Sheet + Console — Product A, system of record) → Call Intelligence (VPS `recordings-archive` —
  Product B, analytics). One VPS/repo/secret/EOS for A+B; the Followup Tracker stands most separate.
- **Tiered KB (D247):** Register (Tier 0, now) + History Archive (Tier 1, history) + `CANONICAL_MANIFEST`
  (Tier 0, the linchpin Phase 0 verifies). Tier 2 = frozen products, **waiver to change** (D34).
- **`clinic_writer` is Tier 2 (frozen).** It is the PC-local, doctor-only vitals + rehab/nutrition
  write-path on `D:\clinic_writer\` — **not** a single static HTML file. Change only under a waiver +
  bump; engine/app/schemas and the print/PDF output are the parts that must never drift.
- **Verification discipline:** a check that cannot fail is not a check; expected values come from the
  artefact, not memory (D188); `node --check` ≠ a functional test (S150).

---

## §2 — Backlog for S151 (the live one)

**Owed from S149 — the doc install/push (owner keyboard). The S150 doc deltas fold into this same set:**
1. **Install the pending doc set into project knowledge + push to GitHub.** The set is the S149 close
   PLUS the S150 deltas: **Register v2.3**, **Archive v1.2**, **Nutrition dossier v1.1**, **this
   Runbook v88**, **START_HERE_SESSION_151**, **regenerated manifest** — plus the still-owed S149
   items (corrected FAR, refreshed README). Then run `Repo_Trim_Phase2_S149.ps1`.
2. **Rule on the 12 held `docs/` files** (current vs superseded) so the Phase-2 tidy can finish.
3. **Recompute the `clinic_writer/` folder digest** on the installed folder (one file changed) and
   re-pin it in the Nutrition dossier + manifest Tier-2 row (currently the specific `vitals_page.html`
   md5 `fcedae30…` is pinned; folder digest `df0b0c34…` is stale).

**Carried (real work):** Insight Harvest items (best calling time, retry-value curve, minimum talk
duration, said-coming vs actually-came) · D223 doctor-portal gist tile (feeds live, build deferred).

**Live-systems Track 2 (when you turn to live work):** WABA sends blocked on the MyOperator authorizer
fault (**D120**, Lokesh) · `wa_approve` still nohup-not-systemd · key rotations overdue.

**Housekeeping:** none pending beyond the install above.

---

## Numbers & sources

Next free: **D249 · F-46 · Session 151.**
Connected: Google Drive · Gmail · Notion ("Clinic HQ") · GitHub (`drmanoj-clinic-automation`). ClickUp parked (D17).

*HANDOFF_RUNBOOK v88 · S150 · supersedes v87.*
