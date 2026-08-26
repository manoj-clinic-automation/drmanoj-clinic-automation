# HANDOFF RUNBOOK — v138 (Session 204 · THE SESSION THAT ASKED WHETHER A PIN IS A BACKUP · 27 Aug 2026)

**Tier 0. §0 what happened · §1 mental models · §2 the live backlog · §3 install discipline · §4 the boundary.**

---

## §0 — WHAT HAPPENED (Session 204 — FULL build EOS)

Opened on the owner's instruction to work unattended wherever possible, and closed on *"do wht is
best, and does not destabilize the system."* Both taken literally: everything below was measured or
built by the assistant; the only two live changes were executed by the owner's own paste.

1. **PHASE 0 GREEN, wider than before.** 208 present rows verified by md5 across all tiers ·
   `md5sum -c` exit 0, 220/220 (**F-119**) · `.gitattributes` still pins `*.md text eol=lf`
   (**F-190**) · project-knowledge headroom **72% used** (was 98% at the S202 close) · and the
   manifest found **byte-identical** in both stores.

2. **F-200 ANSWERED — the inverse check across stores, run for the first time.** 156 documents
   compared both ways against 1,952 repo files. **102 identical · 5 stale in project knowledge ·
   1 stale in the repo · 1 three-way fork with no correct copy anywhere · 45 present only in
   project knowledge**, 44 of which were preserved to `D:\dr-manoj-git\_S204_WORK\pk_only\` with
   `md5sum -c` exit 0. **F-211.**

3. **F-208 — the audit convicted on re-keyed text (ours).** A reported drift in the Diagnostics
   spec was the audit's own transcription dropping a 4-line block — the D114 paragraph that names
   the Fault Register as the authority. The stores are identical. The rule that forbids exactly
   this was already written in `S181_postclose_addendum` §3. **Remedy used thereafter: transcribe
   twice, independently, compare — 42 of 44 converged byte-for-byte.**

4. **D352 — Darpan's ceiling made to agree across both systems.** The ledger already said 50; the
   Sanjeevni drawer had **no `advance.*` settings rows at all** and fell back to a **coded 75**,
   still allowing ₹15,000. Corrected by the owner's paste to ₹10,000 on both sides. **§5.3 of the
   S190 document — open since S190 — is answered:** `staff_master.csv` gives base ₹20,000.

5. **F-209 — a pin is not a backup.** Four live VPS files existed in **one place only**, including
   `finance_app.py`, the clinic's money application. `verify_live_pins.py` was GREEN on all four,
   correctly. **The record is a hash, not the bytes.** Kit `S204_C1` captured 31 files (0 drift,
   0 missing), verified twice against independent references. **`make_force_keys.py` is still
   single-copy** — 38 mobile-shaped strings, correctly refused by the F-185 gate.

6. **F-207 fixed — the file that warns against the fault it commits.** `finance_app.py`'s smoke
   suite says a hardcoded `"15,000.00"` would go red the day the ceiling is revised, and hardcodes
   it sixteen lines below. D352 made it red. Kit `S204_C2`, built **from the live bytes captured
   hours earlier** — impossible before this session. **720/721 → 721/721, projection written first
   and the mechanism checked rather than assumed.**

7. **F-210 — a hash cannot carry a permission.** `mode change 100755 => 100644` on
   `email_agent.py` and `finance_backup.sh` in transit. **A rebuild that verifies GREEN on every
   hash can still produce a backup script that never runs.**

8. **F-212 — two publishers, one repo (ours).** The VPS committed locally, manojz published the
   same content, the histories diverged and a kit delivery failed with a message that named the
   symptom. Fixed by a self-guarding block that proved equivalence before discarding anything —
   and that guard then caught the stray file and the mode change above.

9. **The assistant published for the first time.** Four commits — `5c1cdd8`, `b68507e`, `b0a4c8c`,
   `e2f0407` — each **verified against GitHub's HEAD**, never against the batch file's own output.
   Two pieces of its own mess were recorded rather than quietly cleaned: a `__pycache__` from its
   compile check, and a `.git/index.lock` from its own `git status` that would have blocked the
   owner's next publish.

---

## §1 — MENTAL MODELS (added this session)

- **A pin proves identity, not recoverability. A hash is not a backup.** GREEN on a checker means
  the file matches the record; it says nothing about whether the file could be restored.
- **A hash cannot carry a permission.** Nor ownership. Bytes verified, mode lost, script dead.
- **Re-keyed text may corroborate, never convict.** Two independent transcriptions that agree are
  evidence; one is not — however careful it looked.
- **The newer store is not automatically the right store.** The repo's S190 policy was newer than
  project knowledge's *and still wrong* against the deployed code. Check against what runs.
- **One repo has one publisher.** Any other box is a delivery channel, and a delivery channel must
  not commit.
- **A warning written beside a fault does not prevent the fault.** F-207 sat sixteen lines below
  the comment forbidding it.
- **A guard that stops for a reason you did not anticipate is working.** Both surprises this
  session — the stray file and the mode change — came from a guard refusing to proceed.
- **Where an anchor is deliberately not unique, the count is the check.**
- **"Configured" and "scheduled" have a documentary twin: "recorded" and "recoverable".**

---

## §2 — THE LIVE BACKLOG

> **The maintained copy is `OWNER_TODO_LIVE.md`** (project knowledge, un-manifested by design,
> refreshed at every close as step A10). This is the close-time snapshot.

**⭐0 — owner actions:**

- **Copy the new pin list** — on the VPS:
  `cp /root/deploy/repo/deploy_kits/KB_canon_all/live_pins_S204close.txt /root/deploy/live_pins.txt`
  then `python3 /root/deploy/verify_live_pins.py`. **Until this is done the checker will report
  DRIFT on `/root/finance/finance_app.py`** — correctly: the file moved to `70f79997…` at S204 and
  the old list still carries `7948cee0…`.
- **FIVE RULINGS, all measured and waiting on you:**
  1. **August grandfathering** — does Darpan's new ₹10,000 ceiling bite this month, or does August
     stand at ₹15,000 and 50% start in September? (D331 ruled "applies from AUGUST".)
  2. **F-185, on the corrected figures** — the S204 gate is **stricter than the repository already
     is**: 15 of the 16 files it held back already sit in the public repo in older versions.
  3. **The S190 as-built correction** — confirm the two SL3/SL4 behaviours as your rulings
     (grandfathered pre-D331 rows; interest-bearing loans outside the quota) before they are
     written into the policy document.
  4. **`make_force_keys.py`** — it cannot go into git. Where should the second copy live?
  5. **The 44 preserved single-copy documents** — into the repo, or kept off git?
- **TOKEN ROTATION** (`FINANCE_MARG_TOKEN` + `FINANCE_CRON_TOKEN`) — aging since 21-Aug, **five
  stores not three (F-202)**. Parked at your ruling.
- **TEST ONE RESTORE**, and take a backup of the **previous financial year** (40 days stale, one
  copy). **F-210 makes this sharper: `finance_backup.sh` restored from git will not run until it is
  made executable.**
- **Pravesh exits 31-Aug** · July top-ups Rs 4,519 · Surendra Rs 516 · Arjun · Shivani ·
  **AF-3's scan before the August close**.
- **F-173** — the April-2025 NEFT advice file. Still the only open item where money may already
  have gone to the wrong party.
- **Generate 25-Aug's Marg sale report.**
- **Marg support:** can `margwin.exe` export a named report from the command line, and how is a
  backup scheduled given it holds `D:\MARGERP\Data` open (F-201 settled that it was never
  scheduled).
- **PUBLISH is no longer yours** — the assistant runs `PUBLISH_ALL.bat` and verifies against
  GitHub's HEAD. Say so if you want that back.

**⭐1 — builder queue:**

1. **D350 §4 — the reinstall kits.** The VPS half now has its bytes (`S204_C1`); **the medical PC
   and manojz halves are still owed**, and F-210's `chmod +x` lines belong in both.
2. **D350 §2 / §3** — verification at both ends, measured never inferred; the three B2 states.
3. **F-195** — make the pipeline-gate check actually bite: post the way the caller posts, from an
   unauthenticated client, and prove it RED against the reverted gate.
4. **F-211** — reconcile the five stale documents and the S196 three-way fork, per your rulings.
5. **F-208 structural** — the two-transcription rule belongs in `END_OF_SESSION_PROMPT` (v8), not
   only in this session's memory.
6. **AF-1 (F-206)** — armed in `SEND_TO_CLINIC.bat`; at minimum write the cure where the person at
   the machine can find it.
7. Then: F-183 · identifier capture on the health page · B3–B7 · the ledger kit · F-178 · Staff
   Console Phase 0 (four owner rulings owed) · **Purchase Portal (D335)**.

**⭐2 — the August close** remains the first fully live enforced run — now with the ₹10,000 ceiling
question inside it.

**⭐3 — blocked:** the no-clinic-ID bills → Docterz migration · Lab PC / Labmate ·
**D348 still conflicts with `MARG_INGESTION_REFERENCE_v1` §9 item 5** (unresolved, owner decision).

---

## §3 — INSTALL DISCIPLINE (updated)

Unchanged from v137, plus four earned this session:

- **Verify a publish against the remote, not against the tool.** `PUBLISH_ALL.bat` printing success
  is not evidence; `git ls-remote origin HEAD` equal to the local HEAD is.
- **Where an anchor is deliberately not unique, assert the count.** `S204_C2`'s fifth edit matched
  twice on purpose; the builder required exactly 2 and would have refused on 1 or 3.
- **Say when a red-proof is partial.** `S204_C2`'s failure is a live-data failure and cannot be
  reproduced offline against a fresh store. That was stated, and a predicate-level proof given
  instead — rather than letting an offline green stand in for the thing it does not test (F-195's
  lesson, applied to ourselves).
- **Two independent transcriptions or bytes delivered as a file.** Never one pass (F-208).

---

## §4 — THE BOUNDARY (moved this session, and recorded)

**What moved:** the assistant now **publishes** — `PUBLISH_ALL.bat`, run from the desktop at
click-only tier (Windows blocks typed input to Explorer and to a console, so navigation and a
double-click are the whole capability), with every publish verified against GitHub's HEAD.

**What has NOT moved:** **the owner holds every credential.** The VPS has no GitHub credentials by
design — its push refused this session and the fallback was a tarball the owner carried across. No
token, password or key enters a session. Nothing already live is rebuilt without his explicit OK,
and the manual workflow always stays the fallback. **Live money rules are changed only by his own
paste** — D352 was, on both stores.

---

*HANDOFF_RUNBOOK v138 · written at the S204 close · supersedes v137.*
