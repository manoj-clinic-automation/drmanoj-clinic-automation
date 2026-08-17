# START HERE — Session 186

Hi Claude. Continuing my clinic-automation project (**Session 186**).
I'm Dr. Manoj Agarwal, orthopaedic surgeon, Advanced Orthopaedic Surgery Centre, Bareilly.
Solo practice, older Hindi-first semi-urban patients.

*(Session entry point regenerated at the S185 close. Follow `START_HERE_PROMPT_v5` = the project's
custom instructions. This file carries the Phase-0 pointers current as of S185 and the S186 top task.)*

**Working protocol:** plain language · ONE step at a time, wait for explicit confirmation · full-file
replacements · ALL-CAPS = urgent · mask patient numbers to last-4, never print secrets · nothing live
rebuilt without explicit OK, manual workflow stays the fallback · build/test offline, **rehearse the
installer against a throwaway target**, then install via the **D317 kit chain** · asset + finance apps
use system `/usr/bin/python3` (F-53); `/root/wa` + portal gunicorn use `/root/wa/venv/bin/python3`.

---

## ✅ The canon is CURRENT. There is no documentation debt.

S183, S184 and S185 were all folded in at the S185 close — the first clean handover since S182.
**KB Register v5.6** · **KB History Archive v1.33** · **Fault_Action_Register v2.19** ·
**HANDOFF_RUNBOOK v119** · manifest STATUS **current at S185**. Expect Phase 0 to be quiet.

**One honest gap, deliberately left visible.** The `finance_app.py` live pin is **partial** —
`c66bec2b76…` — because the full md5 was never written down at the S184 close and was **not invented**
at the fold-in. It is ⭐ task 0 below: one command completes it.

## Phase 0 — do this FIRST (verification before work)

**Documents** — one command against git bytes *(a hash verdict is pronounced only on bytes delivered
as a FILE; re-keyed inline text may corroborate, never convict)*:
```
cd /tmp && rm -rf kbv && git clone --depth 1 -q \
  https://github.com/manoj-clinic-automation/drmanoj-clinic-automation.git kbv \
  && cd kbv/deploy_kits/KB_canon_all && md5sum -c MD5SUMS_ALL.txt
```
**Then the F-88 cross-check** — a passing `md5sum -c` proves a kit internally *consistent*, not
*current*. Extract every md5 in `CANONICAL_MANIFEST.md` and match it against the real file hashes; the
tokens that legitimately match no file are live-code pins, Tier-2 artefact digests and the three D316
closed-as-lost rows. **And the NEW inverse check (F-107): confirm every Tier-0 document you are about
to read has a manifest row** — the manifest catches a *wrong* row and is blind to a *missing* one.

**Live code (D321) — owner-run on the box:**
```
python3 /root/deploy/verify_live_pins.py
```

1. Open **`CANONICAL_MANIFEST.md`** and verify every doc row by md5.
2. Read into context only **Tier 0**: manifest, this file, **KB Register v5.6**,
   **HANDOFF_RUNBOOK v119**. No open incident. Open the S183/S184 finance + design docs on demand.
3. Confirm, then start.

## ⭐ S186 TASK 0 — complete the `finance_app.py` pin FROM the box (five minutes)

Run `verify_live_pins.py`. The Register row carries only `c66bec2b76…` and says so openly. Correct it
from the machine (**D321(d): the box wins**), and the Register is whole. This is the only outstanding
record gap in the project.

## ⭐ S186 TASK 1 — resolve the opening float, then book

Get **Darpan's drawer count** + **Dr Bhawna's held cash** into `Sanjeevni_Cash_Reconciliation.xlsx`
Tab 1 → the verdict decides:
- **float ≈ 0** → the 29 negatives are real parking-timing; book nothing (they stay labelled).
- **float ≈ 85–99k** → ship the prepped gated **`S184_C3a`** (opening-float-parked-with-Dr-Bhawna;
  resolves the 29 negatives).

Booking the negatives away is **mathematically impossible at float 0** — the books come up short by
roughly ₹85k, matching the sheet's 8-Apr ₹99,017 injection. So *"no negatives"* and *"drawer ≈ ₹43k"*
cannot both be true, and **only a physical count decides which is.** Don't fabricate a schedule to make
a chart look right. Design + both paths: `S184_Float_Investigation` + **Archive §S184**.

**Then (Runbook v119 §2):** Darpan submits 14/15 Aug with scans, Manoj approves; 16 Aug optional under
D322 · build the reserve/counter-person model (**Hindi labels approved FIRST**) · the reconciliation
workbench (+ the blank-but-flagged drawer-count field; delivers the F-91 fix) · F-104 WALK-IN reclass ·
**F-103 Yes Bank cash-deposit reconciliation** (the deposits were booked, the mechanism was not built) ·
F-106 self-test split · **F-107 / F-108 inverse checks** · F-97 part 2.

## Where the truth lives

- **`CANONICAL_MANIFEST.md`** — doc set / tiers / hashes. STATUS **current at S185**.
- **KB Register v5.6** (now) · **KB History Archive v1.33** (history, §S65–§S185) ·
  **Fault_Action_Register v2.19** (F-0 … F-108, next free **F-109**) · **HANDOFF_RUNBOOK v119** ·
  S183/S184 finance and design docs, opened on demand.
- **Live finance**: `finance.db` corrected (C1a/C2a — cash-in-hand ₹42,993, closing 13 Aug +₹27,654,
  29 real parking days labelled); `finance_app.py` = the D322 classifier, 314/314, **pin partial**.

**Connected sources:** Google Drive · Gmail · Notion · GitHub (`drmanoj-clinic-automation`, PUBLIC by
D320) · ClickUp parked (D17). Patient data is NOT in this project. Sanjeevni scans live in a different
Drive account (not readable here).

**Next free: D323 · F-109 · A-D25 · Session 186.** Cold-kit count **1 of 3–5** (`KB_S185_close` taken
after the fold-in).

*START_HERE_SESSION_186 — regenerated at the S185 close. Supersedes START_HERE_SESSION_185.*
