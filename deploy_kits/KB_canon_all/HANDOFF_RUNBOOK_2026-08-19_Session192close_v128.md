# HANDOFF RUNBOOK — v128 (Session 192 close · 19 Aug 2026)

**Tier 0. §0 what happened · §1 mental models · §2 the live backlog · §3 install discipline · §4 the EOS automation boundary.**

---

## §0 — WHAT HAPPENED (Session 192)

**A five-part session: the KB was freed, three D332 kits went live, the gated money corrections were executed, F6 was stopped at its design on purpose, and a publish warning turned into a finding.**

**1. The KB cleanup** — the owner's own S191-close ruling, run first because project knowledge stood at **96% of its ceiling** and was months from refusing writes. Governing rule, his: *delete only what is proven byte-present in the git canon by md5 at cleanup time; a doc whose bytes exist nowhere else is FILED first or kept; a filename is not provenance (D188).* A fresh anonymous clone, an md5 index of 1,200 files, every candidate's manifest pin cross-checked — plus a **round-trip control** proving the read path byte-exact before a single deletion. **47 documents deleted on one approval; 1,919,222 → 1,149,776 characters (96% → 57.5%).** Five Category-C docs deliberately kept, their bytes not cheaply provable.

**2. Three D332 kits, three installs, each landing first time on its stated number.** `S192_SL5` (218 → 240): the **waiver instrument**, the **policy-date settings**, the **F-151 wording fix**. `S192_SL6` (240 → 274): the **schedule lane** with uneven distributions, **DEFER replacing SKIP**, the **capacity rule**. `S192_SL7` (274 → 287): the **per-staff Perks view**. Pin `470bb113…` → `0ed19495…` → `0279540e…` → **`44e39d6a…`**. All three built on live bytes recovered **by hash, not filename**.

**3. The gated data corrections executed** (D332 §6 items 1–4) on a separate explicit GO, after a **read-only survey** and a **dry run** that printed every intended write. The survey was the point: it proved the three rows reversible AND that **August was not yet closed**, making the ₹10,000 tripwire live rather than historical. Six writes; verified afterwards by re-running the survey, not by assertion.

**4. `S192_F6` designed and deliberately NOT built.** Its smoke suite copies the live `finance.db`, so it cannot run offline; shipping into it on reasoning alone is **F-87** exactly. The survey did establish F6 is narrower than feared — the approval endpoint already says *"Approval is what posts a salary advance to the Staff Ledger. Not entry."* with the call stubbed `PENDING_LEDGER_WIRING`.

**5. Findings.** **F-147 · F-149 · F-150 · F-151 CLOSED** by code now running. **F-148 open** pending F6. **F-152 · F-153 · F-154 minted.**

---

## §1 — MENTAL MODELS (added this session)

- **A warning is a finding.** F-152 came from a line of `PUBLISH_ALL` output nobody had to act on. Nothing was broken; the fault was one commit away and would have surfaced as a **good kit refused by its own gate**.
- **A gate that fires wrongly is worse than no gate.** D316's rule, met twice this session (F-152, F-153). A halt that fires on good input is the halt that gets waved through — and it takes the real ones with it.
- **The files that gate an install are part of the install.** Checksums and identity files inherit the discipline of the code they guard.
- **Test your own arithmetic before you write the test that blesses it.** SL6's first schedule implementation silently ate the final instalment after a defer. It was caught by working the numbers, not by the suite that would have been written to agree with it.
- **Count the checks, do not eyeball them.** Two projections missed this session, both because new `ck(` calls were counted by eye; `ck(False, …)` guards inside `try` blocks never execute. Count programmatically **before** running.
- **Before asking the owner to do it by hand, check what is already connected** (F-154). And **never ship an ellipsis into a terminal** — a placeholder that looks like a path will be pasted as one.
- **A cross-book money writer is the last thing that should ship on a plausible argument.** If its suite cannot run, making it runnable is the first task, not an optional one (F-87, applied rather than quoted).
- **Survey, dry run, then write** — for any correction to live money. The survey is what tells you whether the risk is live or already past.

---

## §2 — THE LIVE BACKLOG

**⭐0 — OWNER, AND IT HAS A CLOCK.** Scan Darpan's **signed written application** against advance row **`0cc0b26b38c5`** (₹20,000, PENDING) and approve it. The D331 gate has no escape hatch. **If it is not approved before the August close runs, no ₹8,000 is collected this month** — the schedule simply shifts. Once approved: August takes ₹8,000 (schedule) + ₹5,000 (loan) = ₹13,000, take-home ₹7,000.

**⭐1 — `S192_F6`, the drawer→ledger bridge (F-148).** First task: build the seeded store from `finance/dev/dev_seed_smoke_db.py`, extended to carry the **live SHAPE** (F-140) — an approved day with a `salary_advance` expense at `ledger_posted=0`, plus a `staff_ref` row. Then baseline, then build, then **differential** verification (zero failures added). Design, mechanism, idempotency guard, write ordering and the fail-loud requirement are all in `S192_F6_Design_and_Survey.md`. **Open question to READ, not assume:** whether `v_day_cash` counts expenses on unapproved days — that decides whether "the drawer is not touched" is already true.

**⭐2 — F-153, one line.** Add the original's `against_month` to the row `make_contra` builds.

**⭐3 — July salary close.** The owner-side sheet (`Salary_July_2026_for_finalisation.xlsx`, deliberately outside the public repo, F-31/D320): waivers + actual-paid, then close. This is the waiver workflow's first real test.

**⭐4 — Darpan's introduction to the Sanjeevni daily entry portal**, and his 17/18 Aug drafts.

**⭐5 — the first real month-end on the new machinery.** Watch the August close: the schedule lane, the capacity rule and the quota lane all fire for the first time together.

**Watch, not owed:** `attendance_enforce_from` is deliberately unset, so July and August are preview-only. Setting it is a policy act, taken when the notice is served.

---

## §3 — INSTALL DISCIPLINE (additions this session)

- **Deliver into the repo, not into a download.** Where a bridge to the owner's machine exists, write kit files straight into `deploy_kits/` (F-154).
- **State the projection in the installer and reconcile any miss out loud** — never retro-fit it to the measured number. Both S192 misses were arithmetic by the assistant, both reconciled against the test block, both kits shipped with the measured figures.
- **Grep the whole gate output, and verify the grep matches real output** before shipping the installer — em-dashes and spacing included.
- **A correction to live money runs survey → dry run → owner's GO**, and the dry run prints every row it would write.

---

## §4 — THE EOS AUTOMATION BOUNDARY (held, unchanged)

The assistant executes the whole close — documents A0–A8, the project-knowledge swap, the repo commit staged onto the PC, the cold kit when due. **The owner's residual work: one `PUBLISH_ALL.bat` double-click and the on-box pin-list copy + verify.** Anything more in a close is a fault in the close.

---

*HANDOFF_RUNBOOK v128 · Session 192 close · supersedes v127. If §0, §2 or this end-marker is absent, this file is truncated and must not be used as canonical.*
