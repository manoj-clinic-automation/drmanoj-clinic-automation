# Fault_Action_Register — append block for F-85 … F-89 (Session 180)

**To be merged into `Fault_Action_Register` → v2.17 (alongside the still-owed F-82+F-83 append and
the F-84 append). §0–§6 lanes unchanged. Full narrative for all four: Archive §S180.**

> **The Fault Register was RECOVERED at the S180 close.** It was unreachable at Phase 0, then found
> by hash-search on the owner's `D:` drive inside the S171 cold kit
> (`DrManoj_Clinic_FULL_Handoff_Session171_2026-08-12\Fault_Action_Register_v2_16.md`,
> md5 `1702b5a8e0663847eaa097919aea94d3`, matching its pin exactly). **All three owed appends can now
> be applied** — F-82+F-83, F-84, and this one — taking it to **v2.17**.

---

## F-85 — a session number was assigned by anticipation instead of by close-out
**Raised:** S180 · **Severity:** low (documentation integrity) · **Status:** CLOSED by correction
**Kin:** D188 (a filename is not provenance), F-54 (audit the artefact, not the label)

**What happened.** Session 180 opened with a document headed *"Session: 181 (follow-on to S180)"*.
Its stated predecessor, `S180_Marg_Folder_Recon`, was written at 09:15 on 15-Aug — **before** the
S179 close-out ran at 10:50. So the recon was S179 work carrying a forward-guessed label, and the
survey that followed inherited the error and advanced it by one.

**Why it matters.** Two documents in project knowledge carried wrong session numbers, and a third
session was about to. Session numbers are how this project's history is indexed; a wrong one sends a
future reader to the wrong Archive section.

**Diagnosis.** Derived from the artefacts, not the labels: the last close-out was S179 and it named
the next session 180; no close-out had run since; therefore no number past 180 had been consumed.

**Fix.** The session was recorded as **180**. The survey was folded in as
`claude/S180_Marg_Feed_Feasibility.md` with a provenance block stating the correction, the original
upload's md5 (`c2086db25b39c02e8c29bc6cf4dc634c`), and the body byte-for-byte verbatim.

**RULE.** A session number is assigned by a **close-out**, never by anticipation. An artefact
produced mid-session carries the number of the session that is actually running.

---

## F-86 — a reader for a PHI source emitted full phone numbers, because it was written against the source's shape rather than the destination's rules
**Raised:** S180 · **Severity:** medium (privacy) · **Status:** FIXED before install
**Kin:** F-31/F-49 (PHI out of repo and kit), F-46 (whitelist-only printing)

**What happened.** `marg_report.py` was built to read Marg's `.xls` and emit bill rows for
`finance_ingest.adapter_csv`. It carried the patient's **full 10-digit phone number** into its CSV,
because the source report prints one and the reader was written to mirror the source.

**Why it matters.** The destination forbids it. `patient_ref` stores **`phone_last4` and nothing
more** — a deliberate masking design — and `ingest_column_map`'s allowed-field list has **no phone
field at all**, so the full number could never have been consumed anyway. It was exposure with no
purpose. Had that CSV been written to disk on the VPS or swept into a kit, it would have been a
fuller PHI leak than the schema's own design permits.

**Fix.** The bill CSV emits `phone_last4` only; the item CSV carries **no patient identity at all**
(the bill number is its only link). Outputs were grepped for any 10-digit string — none found. A
`last4()` helper is now the only way a phone leaves the module, with the reasoning in its docstring.

**RULE.** The destination's constraints are **part of the specification**, not a detail discovered
at install. Before writing a reader, read the schema it feeds.

---

## F-87 — a change was shipped to a test suite that could not be run offline, twice
**Raised:** S180 · **Severity:** HIGH (process) · **Status:** remedied by an asset, not a resolution
**Kin:** **F-84** — *"the offline-testing shortcut was the vulnerability"* — this project's own
lesson, repeated after it had already been minted

**What happened.** `finance_app.py`'s smoke suite is the install gate. It is written against the
real store: >100 filed days, approved and locked days, open exceptions, a legacy tail that leaves
cash negative. None of that existed offline, so the suite **could not be run** here. A test block
was added to it anyway and shipped on reasoning alone. It failed on the box with two broken
assertions — `failed ingest preserved existing lines` and `patient revenue spine populated` — both
caused by the added block. **The install gate rolled it back correctly**; nothing was left
half-installed.

**Two concrete traps, both now written into the code itself:**
1. **`ingest_day` supersedes the day's previous batch and DELETES what it produced.** Any test that
   ingests destroys what earlier tests set up. This trap was hit **twice in one session** — once in
   `finance_ingest.py`'s own selftest, then again in `finance_app.py` after the first lesson.
2. **Resolving a queued line ADDS a `sale_item`**, and an earlier check asserts the day still has
   exactly three lines.

**Fix.** The block no longer calls `/ingest` at all — it inserts its queue row directly, exercising
only the route that changed — and runs **last**, with a comment stating it must stay last and that
new checks go above it.

**The remedy that matters is an asset, not a fix.** `dev_seed_smoke_db.py` builds a database
satisfying the suite's preconditions, so the suite can be run **before** shipping. With it, the
change was verified **differentially** rather than absolutely:

```
unmodified app, seeded db    163/173
modified app,   seeded db    166/176      same 10 seeding artefacts,
                                          +3 new checks, ZERO failures added
```

Then confirmed on the box: **179/179**.

**RULE.** **If a test suite cannot be run, making it runnable is the FIRST task, not an optional
one.** And when a suite's absolute score cannot be trusted (imperfect seeding), verify
**differentially** — baseline versus modified on identical data — rather than chasing a green number.

---

## F-88 — a passing `md5sum -c` proved a kit was internally consistent, not that it was the intended kit
**Raised:** S180 · **Severity:** medium (install integrity) · **Status:** FIXED
**Kin:** D188 (a filename is not provenance), F-66 (trust the hash)

**What happened.** An install kit was corrected and re-issued. Two subsequent install attempts
**ran the older download**, because the browser had saved the new file under a different name and the
original was what reached the box. The installer's `md5sum -c SUMS.md5` **passed both times** — a
stale kit is internally consistent: its checksums match its own files perfectly.

**Why it matters.** The hash gate is the project's primary defence against installing the wrong
bytes, and it silently permitted the wrong build twice. Two debugging rounds were spent looking for
a code fault that had already been fixed.

**Fix.** The installer now carries the **identity of the build it belongs to** — a `KIT` name and
the expected md5 of the file that actually changed — checks it **first**, and refuses to run
otherwise:

```
-- kit: S180_U11c
!! STALE KIT. finance_app.py.new here is ab3dbf52...
!!            this installer expects   7b62b7ae...
!! You are running an older download. Fetch S180_U11c and unzip it again.
```

The guard was tested against the superseded module before shipping. Re-issued kits also take a new
folder and zip name (`_U11b`, `_U11c`) so a browser cannot hand over the old one.

**RULE.** A checksum proves **integrity, never currency**. An install kit states which build it is
and refuses to run if it is not that build.

---

---

## F-89 — the cold-backup cadence lapsed for nine sessions, and three canonical documents were lost
**Raised:** S180 · **Severity:** HIGH (irrecoverable data loss) · **Status:** cause corrected; loss permanent
**Kin:** F-87 (a discipline this project had already written down, not followed)

**What happened.** The S180 Phase 0 found seven canonical rows unreachable. A hash-based recovery
tool was written and run over the owner's `D:` and `C:` drives — searching by **md5 rather than
filename** (D188), opening `.zip` archives, and re-hashing LF-normalised copies of near-misses.
**26,745 files hashed. Four recovered. Three could not be found anywhere and are gone:**
`KB_Asset_Register` v1.11.0 (**Tier-1 CURRENT**), `KB_Register` v5.0, `KB_History_Archive` v1.26.

**Why exactly those three — this is the finding.** The newest full cold kit on the machine is
**`DrManoj_Clinic_FULL_Handoff_Session171`**. The three lost documents are **S177 and S178 outputs**.
Everything up to S171 was comfortably recoverable from disk; everything after it depended on whatever
happened to have been downloaded loose. The four that *were* recovered came from the S171 cold kit,
the S165 cold kit, and the git repo's `canonical-docs/` — all of them backup mechanisms that had run.

`END_OF_SESSION_PROMPT_v4 §E` says a full cold kit is generated *"~3–5 sessions since the last one,
or when the Register/Archive just bumped a version, or when you ask,"* and that it should be
**flagged at close if overdue rather than built unasked**. Nine sessions passed. It was not flagged,
and it was not built.

**The loss was not caused by the Phase 0 that discovered it.** It was caused nine sessions earlier,
by a backup not taken. Phase 0 did its job — it is the only reason anyone found out at all.

**Fix.** Cold-backup discipline restored at this close: `KB_S180_close.zip` contains all six canonical
documents plus `MD5SUMS.txt`, and the git kits were committed, clearing a two-session lag.

**RULE.** **The cold kit is not discretionary.** It is a standing backlog item carrying a session
count, and that count is checked at every close — not consulted only when something is already
missing. A backup regime whose failure is invisible until a document is needed is not a backup regime.

**Consequence, recorded under D316:** the two historical losses are closed **LOST-SUPERSEDED**
(v5.1 and v1.27 are verified present, nothing current depends on them). `KB_Asset_Register` v1.11.0
is closed **LOST-RECONSTRUCTABLE** — the recovered v1.10.3 plus Archive §S173–§S177 can rebuild it.
It is unbuilt, not unknowable.

---

*Next free finding number after this append: **F-90**.*
