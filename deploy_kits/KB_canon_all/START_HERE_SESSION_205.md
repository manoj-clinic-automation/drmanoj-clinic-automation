# START HERE — SESSION 205

Hi Claude. Continuing my clinic-automation project (**Session 205**).
I'm Dr. Manoj Agarwal, orthopaedic surgeon, Advanced Orthopaedic Surgery Centre, Bareilly.
Solo practice, older Hindi-first semi-urban patients.

**Working protocol (follow strictly):**

- Plain language, no assumed coding knowledge.
- ONE step at a time — wait for my explicit confirmation before the next.
- Full-file replacements only, never diffs I have to hand-edit.
- ALL-CAPS from me = urgent.
- Mask all patient numbers (last-4 only) and all secrets/tokens — never print them.
- Nothing already live is rebuilt without my explicit OK. Manual workflow always stays as fallback.
- Build/test offline → **`py_compile` AND `pyflakes`** (I use `python`, not `python3`) → then install.
- For VPS python, always use `/root/wa/venv/bin/python3`.
- **ALWAYS give me the COMPLETE path, and say which machine it is on.** Full URLs, full paths.
- **A COPY BLOCK IS THE DEFAULT FOR EVERY MACHINE.** One block per machine, never mixed.
- **WHERE YOU HAVE WRITE ACCESS, DO IT YOURSELF.** `D:\dr-manoj-git` and `D:\Downloads` on manojz are
  connected, and **you publish**: `PUBLISH_ALL.bat` is yours now (S204), run from the desktop at
  click-only tier — **and every publish is verified against GitHub's HEAD, never against the batch
  file's own output.** The VPS is mine alone: it holds no credentials by design, so its push
  refuses and a tarball is the fallback.

---

## PHASE 0 — DO THIS FIRST. Verification before work.

1. Open **`CANONICAL_MANIFEST.md`** (Tier 0 · the linchpin) — current at the **S204 close**.
2. **Verify every row by md5 — ALL TIERS.** A row listed as *present* whose hash does not match
   **halts work until reconciled** (D172/D188). **A filename is not provenance (D188).**
3. **Read into context ONLY Tier 0:** the manifest, this START_HERE, **KB Register v5.56**,
   **HANDOFF_RUNBOOK v138**, and any open incident. **Tier 1 on demand. Tier 2 hash-verified,
   never read, never edited without a waiver (D34).**
4. Standing checks: **F-88** · **F-107 inverse** · **F-119** (`md5sum -c` exit 0) · **F-123** ·
   **A8** · **F-190** (`.gitattributes` still pins `*.md text eol=lf`) · **and report
   project-knowledge headroom** (72% used at the S204 close, 1,446,959 of 2,000,000 bytes).
5. **`verify_live_pins.py` — expect GREEN against `live_pins_S204close.txt`.**
   **If I have not yet copied it to `/root/deploy/live_pins.txt`, that is the FIRST thing to tell
   me** — and until I do, the checker reports **DRIFT on `/root/finance/finance_app.py`**, which is
   correct: the file moved to `70f79997…` at S204.
   **Know what it cannot see:** it runs on the VPS. **Every manojz and medical-PC row is blind to it
   by construction (F-186).** And now also know what GREEN does *not* mean: **a pin proves identity,
   not recoverability (F-209).**
6. Then confirm, and start on ⭐1 — but **the five rulings in ⭐0 are mine and several of the ⭐1
   items wait on them.**

---

## WHERE THE TRUTH LIVES

- **`CANONICAL_MANIFEST.md`** — the doc set, tiers and hashes. WINS on "what is canonical / current."
- **KB Register v5.56** (Tier 0) · **KB History Archive v1.51** (Tier 1, §S204 last) ·
  **HANDOFF_RUNBOOK v138** (Tier 0) · **Fault_Action_Register v2.43** (F-0 … F-212).
- **`OWNER_TODO_LIVE.md`** — the always-current owner list, deliberately un-manifested.
- **`deploy_kits/S204_VPS_LIVE/`** — the live VPS bytes, captured at S204 with `SUMS.md5` and a
  MANIFEST carrying **`chmod +x` restore lines (F-210)**.
- **`D:\dr-manoj-git\_S204_WORK\`** — this session's working papers: the F-200 reconciliation, the
  pin record, and `pk_only\` (44 documents that existed only in project knowledge). **Outside git
  on purpose, pending my F-185 ruling.**
- Marg/medical (D351): **`MARG_MEDICAL_CURRENT.md`** in the ordinary loop ·
  `MARG_MEDICAL_HISTORY.md` on demand · `MARG_WALL_CARD.html` printed · `MARG_REPORT_EXPECTATIONS.md`.

---

## WHAT S204 DID (one paragraph)

The session that asked whether a pin is a backup. **F-200 answered**: 156 documents compared across
both stores, drift found in **both directions**, one three-way fork where no correct copy exists
anywhere, and 45 documents living only in project knowledge — 44 preserved to disk (**F-211**).
**Four live VPS files were found to exist in one place only** including the money application, with
the pin checker GREEN on all four and right to be (**F-209**); kit `S204_C1` captured 31 of them.
**D352**: Darpan's 75% exception retired, and the Sanjeevni drawer — which had **no settings rows at
all** and fell back to a coded 75 — brought to ₹10,000 to match the ledger. **F-207**: the smoke
suite's warning against a hardcoded ceiling sits sixteen lines above the hardcoded ceiling; fixed in
`S204_C2`, **720/721 → 721/721**. And **F-208**: the audit itself convicted on re-keyed text and
reported a drift that did not exist.

---

## ⚠ WHAT S204 GOT WRONG, SO IT IS NOT REPEATED

- **The audit convicted on re-keyed text (F-208)** — and `S181_postclose_addendum` §3 had already
  forbidden exactly that. **Two independent transcriptions, or bytes delivered as a file.**
- **"Copy the newer store over the older" was proposed and was wrong.** The repo's S190 policy is
  newer than project knowledge's **and still misdescribes the deployed code**. The owner caught this
  by asking for the deployed check first. **Check against what runs.**
- **Two publishers, one repo (F-212).** The VPS was told to push and then the same content was
  published from manojz; the histories diverged and a delivery failed. **A delivery channel must not
  commit.**
- **The assistant's own leavings needed cleaning twice** — a `__pycache__` inside the repo and a
  `.git/index.lock` that would have blocked the owner's publish. Both recorded, not quietly swept.

---

## ⭐1 — THE BUILDER QUEUE

1. **D350 §4 — the reinstall kits.** The VPS half has its bytes now; **the medical PC and manojz
   halves are owed**, and F-210's `chmod +x` lines belong in both.
2. **D350 §2 / §3** — verification at both ends, measured never inferred; the three B2 states.
3. **F-195** — make the pipeline-gate check bite, and prove it RED against the reverted gate.
4. **F-211** — reconcile the five stale documents and the S196 fork, on my rulings.
5. **F-208 structural** — put the two-transcription rule into `END_OF_SESSION_PROMPT` v8.
6. **AF-1 (F-206)** — armed in `SEND_TO_CLINIC.bat`; at minimum write the cure where the person at
   the machine can find it.
7. Then: F-183 · identifier capture · B3–B7 · the ledger kit · F-178 · Staff Console Phase 0 ·
   **Purchase Portal (D335)**.

---

## ⭐0 — MY ACTIONS

1. **Copy `live_pins_S204close.txt` → `/root/deploy/live_pins.txt`** on the VPS and run the checker.
2. **FIVE RULINGS:** August grandfathering for Darpan's ceiling · **F-185** on the corrected figures
   (the S204 gate is stricter than the repo already is) · the S190 SL3/SL4 as-built wording · where
   **`make_force_keys.py`** should live · whether the **44 preserved documents** enter the repo.
3. **TOKEN ROTATION** — five stores, not three (F-202). Parked at my ruling.
4. **TEST ONE RESTORE** + the previous financial year's backup (40 days stale, one copy) — and note
   **F-210**: `finance_backup.sh` restored from git will not run until it is made executable.
5. **Pravesh exits 31-Aug** · July top-ups Rs 4,519 · Surendra Rs 516 · Arjun · Shivani ·
   **AF-3's scan before the August close**.
6. **F-173** — the April-2025 NEFT advice file.
7. **Generate 25-Aug's Marg sale report.**
8. **Marg support** — command-line export, and how to schedule a backup.

---

**Next free: D353 · F-213 · A-D25 · Session 205.**
**Backlog pointer: `HANDOFF_RUNBOOK v138 §2` (close-time snapshot) · `OWNER_TODO_LIVE.md` (live).**
**Cold kit: taken at the S204 close — `DrManoj_Clinic_FULL_Handoff_Session204_2026-08-27.zip`.**

*START_HERE_SESSION_205 · written at the S204 close · supersedes 204.*
