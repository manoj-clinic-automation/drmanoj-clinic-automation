# START HERE — SESSION 207

Hi Claude. Continuing my clinic-automation project (**Session 207**).
I'm Dr. Manoj Agarwal, orthopaedic surgeon, Advanced Orthopaedic Surgery Centre, Bareilly.
Solo practice, older Hindi-first semi-urban patients.

**Working protocol (follow strictly):**
- Plain language, no assumed coding knowledge.
- ONE step at a time — wait for my explicit confirmation before the next.
- Full-file replacements only, never diffs I have to hand-edit.
- ALL-CAPS from me = urgent.
- Mask all patient numbers (last-4 only) and all secrets/tokens — never print them.
- **ALWAYS use IST.** Never report UTC.
- ALWAYS give the COMPLETE path and name the machine. ALWAYS give commands as a copy block,
  one block per machine.
- Nothing already live is rebuilt without my explicit OK. Manual workflow always stays as fallback.
- Build/test offline → `py_compile` (I use `python`, not `python3`) → then I install.
- For VPS python, always use `/root/wa/venv/bin/python3`.
- **`where git` FAILS on manojz.** Never hand me a bare `git` command — `PUBLISH_ALL.bat` carries
  four fallback paths for `git.exe` and is the one publisher (F-212).

---

## PHASE 0 — DO THIS FIRST. VERIFICATION BEFORE WORK (D247).

1. Open **`CANONICAL_MANIFEST.md`** (Tier 0 · the linchpin).
2. **Verify every row by md5** — hash-compare only, all tiers. A row whose hash does not match
   **halts work until reconciled** (D172/D188). **A filename is not provenance.**
3. **Read into context only Tier 0:** the manifest, this file, the **KB Register v5.57**, the
   **HANDOFF_RUNBOOK v140**, and any open incident. Tier 1 on demand; Tier 2 never without a
   waiver (D34).
4. **A0 — the evidence rule.** Re-keyed text may corroborate; it may never convict. Any claim that
   two copies differ rests on bytes hashed or two independent transcriptions that agree.
5. Then confirm, and ask which backlog item to start (**HANDOFF_RUNBOOK §2**, and
   **`OWNER_TODO_LIVE.md`** for the live truth).

---

## WHERE THE KNOWLEDGE LIVES — FOUR STORES, ONE RULE

| store | authoritative for | reach |
|---|---|---|
| **project knowledge** | **canon** — Tier 0/1, everything `CANONICAL_MANIFEST.md` names | every surface |
| **GitHub** `drmanoj-clinic-automation` | **code**, plus `deploy_kits/KB_canon_all/` — the one folder `verify_live_pins.py` reads | every surface, *if the sync filter includes it* |
| **`D:\Downloads\ClaudeCowork\`** | everything canon excludes + dated frozen snapshots — cold backups, session kits, working papers, raw data | **manojz and Cowork only** |
| **Google Drive** (`drmka.ortho@gmail.com`) | a **one-way mirror** of that folder | every surface |

**THE ONE HARD RULE: no document may be live and editable in two stores.** That is D202, and F-201
states it exactly — *neither store is authoritative by position; compare by md5, never by where a
file sits.* Frozen snapshots are exempt: a cold backup is a copy by definition, and
`KB_canon_all/` is a sanctioned second copy the pin checker requires.

**Start here for the folder:** `D:\Downloads\ClaudeCowork\00_INDEX.md`, and
`D:\Downloads\ClaudeCowork\EXTENSION_PLAN.md` before moving anything into it.

✅ **DONE AT THE S206 CLOSE — the KB History Archive is no longer in project knowledge.**
At 938,390 bytes it was **46.9 % of the 2 MB cap**, for a Tier-1 file Phase 0 is told not to read.
Removing it took the project from **78.9 % to 65.3 %** — 271,921 bytes freed.
⚠ **AND THE PROJECTED SAVING WAS WRONG — measured after the fact, recorded not silently fixed.**
Removing a **938,390-byte** file took project knowledge from **1,578,534 (78.9 %) to 1,306,613
(65.3 %)** — it freed **271,921 bytes, 13.6 points, not the 47 that were projected.**
**`knowledge_size` is NOT the sum of raw file bytes**; it is an indexed measure, and a large
document costs far less of it than its size on disk. The projection assumed the naive model and
was asserted before it was measured — **the A0 fault, committed while writing the rule about it.**
**Plan future capacity from a measured `knowledge_size` delta, never from file sizes.**


**Verify it against any of four copies, all hashed `87cdd56b5259793224754b0a47ee0dd3` at the close:**
`deploy_kits/KB_canon_all/` in git · `D:\Downloads\ClaudeCowork\00_CANON_SNAPSHOT_S206\` · and inside
`DrManoj_Clinic_FULL_Handoff_Session206_2026-08-27.zip` (in `D:\Downloads\` and in
`D:\Downloads\ClaudeCowork\01_COLD_BACKUPS\`).

⚠ **DO NOT "FIX" THIS BY ADDING `deploy_kits/` TO THE GITHUB SYNC FILTER.**
**Synced GitHub files consume the same 2 MB cap as project documents.** `KB_canon_all/` alone
previews at **599 % of capacity** — it holds every historical version ever written (44 Registers,
23 Archives, 29 Fault Registers). Selecting it would push the project to **705 %** and force real
canon out to fit. *This was proposed at the S206 close and withdrawn when the owner's own screenshot
showed the number. Recorded so it is not proposed again.*

**Portability is Google Drive's job, not GitHub's** — a connector reads on demand and stores
nothing, so it costs no capacity. **OWED: put the Archive on Drive** (one drag from
`D:\Downloads\ClaudeCowork\00_CANON_SNAPSHOT_S206\`). Until then the Archive is reachable from manojz and
Cowork but **not from a phone or browser.**

---

## WHAT IS CURRENT AS AT THE S206 CLOSE

| | |
|---|---|
| KB Register | **v5.57 (S206 close)** |
| KB History Archive | **v1.53** — §S206 appended and **§S205 folded in**, both pure-append proven. ⚠ **NOT in project knowledge** — see above for its four locations |
| HANDOFF_RUNBOOK | **v140** |
| Fault Action Register | **v2.44** |
| Close-out routine | **END_OF_SESSION_PROMPT v9** (A12: the Cowork folder, the Drive mirror, and a required report of how full project knowledge is) |

**Next free: D353 · F-232 · A-D25 · Session 207.**
⚠ **F-213 … F-231 are UNRATIFIED.** F-213–F-217 minted at S205; F-218–F-222 and F-223–F-231 are
candidates. **The fork needs your ruling before any new F-number is minted.**

---

## ⚠ TWO THINGS TO RAISE AT THE OPEN

**1. ✅ §S205 IS NOW IN THE ARCHIVE.** The S205 close never ran A1 or A2; the gap was found by
measurement at the S206 close and **folded in as Archive v1.53**, assembled from that session's own
contemporaneous documents — principally Runbook v139 §0 — and **marked in the text as a fold, not an
original.** Where the fold and those documents disagree, **they win.** Nothing was written from memory.

**2. 🔴 Four `FINANCE_*` tokens were printed in chat at S206 and must be rotated** — and there are
**six stores, not five** (the VPS unit holds `FINANCE_MARG_TOKEN` **twice**, and systemd takes the
last, so an edit that stops at the first match leaves the live one untouched).

---

## THE SANJEEVNI WORK — WHERE IT LIVES

**S206 reconciled every item, 1-Apr-2026 → 26-Aug-2026.** 285 items moved, 239 balance exactly,
residue **0.98 %**, all 46 named.

- **`S206_ITEM_LEDGER_RECONCILIATION`** — the wholesome reference
- **`S206_MARG_SANITISATION_AND_DUPLICATES`** — the 10-step plan, duplicates, the two-list diff
- **`S206_RECONCILE_FINDINGS`** — F-223 … F-231
- **`S206_SANJEEVNI_COVERAGE_ADDENDUM`** — every Sanjeevni doc, and which S206 papers are superseded
- **`S206_WORKING_PAPERS_INDEX`** — **six S206 documents are superseded outright; read the index
  before opening any S206 working paper**

**Code:** `deploy_kits/S206_SANJEEVNI_RECONCILE` (47 selftest + 8 verification checks) and
`deploy_kits/S206_SANJEEVNI_MARG_PURCHASE`. **`S###_SANJEEVNI_<thing>` is the naming convention.**

**Self-contained kit:** `D:\Downloads\S206_SANJEEVNI_SESSION_KIT\` — 190 files including 46 raw
Marg exports. Rebuilds every figure with no project knowledge at all.

---

## THE FIRST THING TO ASK ME

**"Ravi's May and August bills, and did Amir explain ETOZOX 90?"** — those two close most of the
remaining 0.98 %. Then: which backlog item.

---
*START_HERE_SESSION_207 · generated at the S206 close, 27-Aug-2026 IST.*
