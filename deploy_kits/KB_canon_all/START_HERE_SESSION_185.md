# START HERE — Session 185

Hi Claude. Continuing my clinic-automation project (**Session 185**).
I'm Dr. Manoj Agarwal, orthopaedic surgeon, Advanced Orthopaedic Surgery Centre, Bareilly.
Solo practice, older Hindi-first semi-urban patients.

*(Session entry point regenerated at the S184 close. Follow `START_HERE_PROMPT_v5` = the project's
custom instructions. This file carries the Phase-0 pointers current as of S184 and the S185 top task.)*

**Working protocol:** plain language · ONE step at a time, wait for explicit confirmation · full-file
replacements · ALL-CAPS = urgent · mask patient numbers to last-4, never print secrets · nothing live
rebuilt without explicit OK, manual workflow stays the fallback · build/test offline, **rehearse the
installer against a throwaway target**, then install via the **D317 kit chain** · asset + finance apps
use system `/usr/bin/python3` (F-53); `/root/wa` + portal gunicorn use `/root/wa/venv/bin/python3`.

---

## Phase 0 — do this FIRST (verification before work)

**Documents** — one command against git bytes:
```
cd /tmp && rm -rf kbv && git clone --depth 1 -q \
  https://github.com/manoj-clinic-automation/drmanoj-clinic-automation.git kbv \
  && cd kbv/deploy_kits/KB_canon_all && md5sum -c MD5SUMS_ALL.txt
```
**Live code (D321):**
```
python3 /root/deploy/verify_live_pins.py
```
1. Open **`CANONICAL_MANIFEST.md`**. ⚠ **It still reads "current at S183"** — the S184 canonical
   fold-in was deferred (see the ⭐ housekeeping below). Verify every doc row by md5 as usual.
2. **`verify_live_pins.py` WILL report DRIFT on `finance_app.py`** — the box is now **`c66bec2b…`**
   (S184_F1b, the D322 classifier); the Register still pins `86382f62…`. This drift is EXPECTED.
   Correct the Register **FROM the box** (D321), never the reverse.
3. Read into context only **Tier 0**: manifest, this file, **KB Register v5.5**,
   **HANDOFF_RUNBOOK v118**, and the S184 finance docs on demand. No open incident.
4. Confirm, then start with the ⭐ housekeeping, then the backlog (Runbook §2).

## ⭐ S185 OPENING HOUSEKEEPING — owed canonical fold-in (do FIRST; debt compounded from S183)
S184 shipped live code + data but did not fold the canon. Apply, precisely:
- **KB History Archive**: append **§S183 AND §S184** (v1.30 → v1.32). *(S183's own append was deferred to S184 and also not done — do both.)*
- **Fault_Action_Register**: apply **F-100–F-104 (S183)** + **F-105, F-106 (S184)** (v2.18 → ~v2.20).
- **KB Register** v5.5 → **v5.6**: correct live pin `finance_app.py` → `c66bec2b76…` (from the box);
  record markers `migration.S184_cash_correction`, `migration.S184_C2a_exceptions`; **D322** into the
  decisions index; **F-105/F-106** into the findings index; C1a/C2a/F1b live-state.
- Rebuild **CANONICAL_MANIFEST** + **MD5SUMS**; promote START_HERE 184 → 185. Then a cold kit (§E).

## ⭐ S185 TOP TASK (after housekeeping) — resolve the opening float, then book
Get **Darpan's drawer count** + **Dr Bhawna's held cash** into `Sanjeevni_Cash_Reconciliation.xlsx`
Tab 1 → the verdict decides:
- **float ≈ 0** → the 29 negatives are real parking-timing; book nothing (they stay labelled).
- **float ≈ 85–99k** → ship the prepped gated **`S184_C3a`** (opening-float-parked-with-Dr-Bhawna;
  resolves the 29 negatives). Design + both paths: `S184_Float_Investigation` + Runbook §0 Thread 5.

**Then (Runbook §2):** Darpan submits 14/15 Aug with scans (Manoj approves), 16 Aug optional ·
**build the reserve/counter-person model** (show Hindi labels for approval FIRST) · the reconciliation
workbench (+ the blank-but-flagged drawer-count field) · F-104 WALK-IN reclass · split the finance
self-test logic-vs-fixture (F-106 follow-up).

## Where the truth lives
- **`CANONICAL_MANIFEST.md`** — doc set/tiers/hashes (STATUS to advance to S184 after the fold-in).
- **KB Register v5.5** (→ v5.6 owed) · **KB History Archive v1.30** (→ v1.32 owed) ·
  **Fault_Action_Register v2.18** (→ ~v2.20 owed) · **HANDOFF_RUNBOOK v118** · S184 finance/design docs.
- **Live finance**: `finance.db` corrected (C1a/C2a); `finance_app.py` = `c66bec2b` (D322 classifier).

**Connected sources:** Google Drive · Gmail · Notion · GitHub (`drmanoj-clinic-automation`, PUBLIC by
D320) · ClickUp parked (D17). Patient data is NOT in this project. Sanjeevni scans are in a different
Drive account (not readable here).

**Next free: D323 · F-107 · A-D25 · Session 185.** Cold-kit count 3 of 3–5.

*START_HERE_SESSION_185 — regenerated at the S184 close. Supersedes START_HERE_SESSION_184.*
