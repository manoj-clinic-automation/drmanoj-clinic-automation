# START HERE — SESSION 204

Hi Claude. Continuing my clinic-automation project (**Session 204**).
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
  New at S203: `py_compile` proves a file parses, not that it runs — a `NameError` shipped twice past
  it. Both, every time.
- For VPS python, always use `/root/wa/venv/bin/python3`.
- **ALWAYS give me the COMPLETE path, and say which machine it is on.** Full URLs. Full paths.
  Every time.
- **A COPY BLOCK IS THE DEFAULT FOR EVERY MACHINE** — my ruling at the S203 close: *"copy block
  please, and make it default everywhere."* One block per machine, never mixed. This supersedes the
  deliver-a-`.bat`-to-double-click habit.
- **WHERE YOU HAVE WRITE ACCESS, INSTALL IT YOURSELF** rather than handing me work. `D:\Downloads` on
  manojz is connected; `S203_R3` was installed that way at S203. Bring me decisions and results, not
  keystrokes.
- **Prefer ONE file I double-click over a sequence of GUI steps** only where no copy block and no
  direct write is possible.

---

## PHASE 0 — DO THIS FIRST. Verification before work.

1. Open **`CANONICAL_MANIFEST.md`** (Tier 0 · the linchpin) — current at the **S203 close**.
2. **Verify every row by md5 — ALL TIERS.** Hash-compare only; it is cheap. A row whose hash does not
   match **halts work until reconciled** (D172/D188). **A filename is not provenance (D188).**
3. **Read into context ONLY Tier 0:** the manifest, this START_HERE, **KB Register v5.55**,
   **HANDOFF_RUNBOOK v137**, and any open incident. **Tier 1 on demand only. Tier 2 is hash-verified
   and never read in the loop**, and never edited without an explicit waiver (D34).
4. Standing checks: **F-88** · **F-107 inverse** · **F-119** (`md5sum -c` must exit 0) · **F-123** ·
   **A8** · **F-190** (confirm `.gitattributes` still pins `*.md text eol=lf` — without it 192 of 208
   canon files change hash on a default Windows checkout and Phase 0 fails on all of them at once) ·
   **and report project-knowledge headroom** (it hit 98% at the S202 close with nothing watching it;
   18 documents were retired at S203 under D351).
5. **`verify_live_pins.py`** — expect **GREEN against `live_pins_S203close.txt`**. If I have not yet
   copied it to `/root/deploy/live_pins.txt`, **that is the first thing to tell me.**
   **Know what it cannot see:** the checker runs on the VPS. **Every manojz and medical-PC row is
   BLIND to it by construction (F-186)** — including the seven medical-PC pins taken for the first
   time at S203. Those must be re-read **from the machine**, never inferred from manojz's mirror,
   which is `robocopy /E` with **no `/PURGE`** and can only be true about what was added (F-199).
6. Then confirm, and start on ⭐1 below.

---

## WHERE THE TRUTH LIVES

- **`CANONICAL_MANIFEST.md`** — the doc set, tiers and hashes. WINS on "what is canonical / current."
- **KB Register v5.55** (Tier 0) · **KB History Archive v1.50** (Tier 1, §S203 last) ·
  **HANDOFF_RUNBOOK v137** (Tier 0) · **Fault_Action_Register v2.42** (F-0 … F-206).
- **`OWNER_TODO_LIVE.md`** — the always-current owner list, deliberately un-manifested.
- **`S202_Marg_Transport_Resilience_D350_CONTRACT.md`** — written, and **scoped by me to §2/§3/§4/§5.
  The Drive fallback (§1) is PARKED. §5 was done at S202 — verify, do not redo.**
- **Marg/medical (D351, new at S203): exactly THREE documents.**
  **`MARG_MEDICAL_CURRENT.md`** is the only one opened in the ordinary loop ·
  **`MARG_MEDICAL_HISTORY.md`** append-only, on demand · **`MARG_WALL_CARD.html`** printed, beside the
  medical PC · plus **`MARG_REPORT_EXPECTATIONS.md`** (a spec, not a record).
  **The three rules: new knowledge EDITS `CURRENT` and the replaced text moves to `HISTORY` — never a
  new file · a session's output is a change to `CURRENT` or an entry in `HISTORY`, session records are
  not canon · anything written to work something out is a WORKING PAPER, stamped at birth and folded
  at the close.**
- **`deploy_kits/S203_MARG_CANON/`** — 67 files, `md5sum -c` exit 0: the preserved set the 18 retired
  project documents came from. **Preserve before you retire.**
- Marg references (Tier 1): `MARG_PIPELINE_REFERENCE_v1` · `MARG_INGESTION_REFERENCE_v1` ·
  `MARG_PIPELINE_MAINTENANCE_FLOW_v1`.

---

## WHAT S203 DID (one paragraph)

The session that looked at the machines themselves. **A chain of three faults, each visible only
because the one before it was fixed:** the pull got a log (**F-197**) → its first log ever kept ended
in a `401` that had printed on **every pull since S202** (**F-194**) → `/finance/api/pipeline-status`
had been added as a route at S202 and **never added to `_gate()`'s exemption list**, so **B2, the
pipeline heartbeat, had never once reported.** Proven both ways, then from the real caller. **The
first medical-PC pins ever taken** — drift there had been undetectable by construction. **F-191(c)
overturned by measurement: the automatic backup was never *scheduled*** — the offsite leg was built
and **proven unattended at 19:37**. **D351 minted** — sixty-nine Marg/medical documents to three,
preserved first and retired second. Three transport kits live on manojz, the VPS gate fixed
(**719 → 721**). **F-194 … F-206 minted; five are the assistant's own.** **D347 amended: Tailscale is
the SOLE transport.**

---

## ⚠ WHAT S203 GOT WRONG, SO IT IS NOT REPEATED

- **AF-1 WAS NEARLY STRUCK AGAINST THE WRONG FILENAME (F-206). IT IS LIVE AND ARMED.** The record said
  AF-1 sat in `GUARD_AND_SEND.bat`; that file is not on the medical PC; the close proposed to strike
  it. **Refused on the current bytes.** `GUARD_AND_SEND.bat` contains no `curl`, `last_response`,
  `sent_hashes`, `ACCEPTED-FOR-REVIEW` or `http_code` — **the mechanism was never in it.** It is in
  **`SEND_TO_CLINIC.bat`, live at `e19a8a777ac22fe75a242f1eb9762185`**: `%RESP%` is not deleted before
  `curl`, the `ACCEPTED-FOR-REVIEW` test never consults `%HTTP%`, and a false accept blacklists that
  report **for ever** in `sent_hashes.txt`. **That file is the only medical-side fallback D347
  preserves. Do not repeat the claim that AF-1 cannot fire.**
- **The check written to close the gate hole does not bite (F-195).** Reverting the gate still gives
  721/721. **A test must post the way the caller posts** — a signed-in test client is not the caller.
- **Project knowledge was the stale store, not the repo (F-200).** **Neither store is authoritative by
  position** — compare by md5, never by where a file sits. An inverse check across stores is owed.
- **A `NameError` shipped twice** because an insertion anchor matched in two places — **an anchor that
  is not unique is not an anchor** — and `py_compile` cannot catch it. **pyflakes can.**
- **`trap … EXIT` pasted into an interactive shell**, so a reverted file sat on disk while it was
  believed restored. **A rollback in an interactive paste must be an explicit command, never a trap.**
- **Thirteen documents produced while consolidating sixty-nine away (F-205).** D351's working-paper
  rule exists because of this.

---

## ⭐1 — WHAT I WANT NEXT, AND IN THIS ORDER

**1. D350 §2/§3/§4 — THE REINSTALL KITS FIRST.** §4: the reinstall kit, **Marg and its data first**,
the pipeline second — if either PC dies, this is what rebuilds it. Then §2 verification at both ends,
**measured, never inferred**. Then §3 what B2 must show. **§1 the Drive fallback stays PARKED. §5 was
done at S202 — verify, do not redo.** Work **max on your own**: survey, design and build offline;
install where you have write access; bring me decisions and results.

**2. F-195 — make the pipeline-gate check actually bite.** Post from an unauthenticated client, the
way the caller posts, and **prove it RED against the reverted gate** before it counts as coverage.

**3. F-200 — the inverse check across stores.** Every document in both project knowledge and the repo,
compared by md5, differences reconciled.

**4. AF-1 (F-206).** Either check `%HTTP%` before the ACCEPTED branch and delete `%RESP%` before
`curl`, or at minimum put the cure — deleting one line from `sent_hashes.txt` — somewhere the person
standing at the machine can find it. Today it is written nowhere.

Then: F-183 · identifier capture on the health page · B3–B7 · the ledger kit · F-178 · Staff Console
Phase 0 (my four rulings owed) · **Purchase Portal (D335)** as the other flagship.

---

## ⭐0 — MY ACTIONS

1. **PUBLISH** — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` on manojz. The S203 close
   is committed locally only until I do.
2. **Copy `live_pins_S203close.txt` → `/root/deploy/live_pins.txt`** on the VPS and run the checker.
   Publish first.
3. **TOKEN ROTATION** — parked at my ruling, but **it lives in FIVE stores, not three (F-202)**.
4. **TEST ONE RESTORE**, and take a backup of the **previous financial year** — 40 days stale, one
   copy.
5. **Pravesh exits 31-Aug** · July top-ups Rs 4,519 · Surendra Rs 516 · Arjun · Shivani ·
   **AF-3's scan before the August close**.
6. **F-173** — the April-2025 NEFT advice file. Money may already have gone to wrong accounts.
7. **Generate 25-Aug's Marg sale report.**
8. **F-185** — the repo visibility ruling is mine, on the corrected figures.
9. **Marg support:** can `margwin.exe` export a named report from the command line — and **how do I
   schedule a backup**, given `margwin.exe` holds `D:\MARGERP\Data` open. (Not "why does it fail":
   F-201 settled that. It was never scheduled.)

---

**Next free: D352 · F-207 · A-D25 · Session 204.**
**Backlog pointer: `HANDOFF_RUNBOOK v137 §2` (close-time snapshot) · `OWNER_TODO_LIVE.md` (live).**
**Cold kit: last taken at the S202 close (per START_HERE_SESSION_203); nothing recorded at S203 — check whether one is due.**

*START_HERE_SESSION_204 · written at the S203 close · supersedes 203.*
