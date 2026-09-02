# FAULT → ACTION REGISTER — v2.48 (CONSOLIDATED, SELF-CONTAINED) *(H1 corrected of record at the S219 open: it had read v2.43 through v2.44–v2.47 — the F-45 family; recorded, not silent)*
## Advanced Orthopaedic Surgery Centre, Bareilly
**Owner: Dr. Manoj Agarwal · Maintained with: Claude**
**Drafted Session 63 · Re-based Session 131, 09 July 2026. Supersedes v1 entirely.**
**v2.48, Session 219 OPEN (the S217/218 fold), 02 September 2026 — F-269 … F-275 appended.** The marathon's seven roots: a smoke suite writing fixtures into the live store since S179 (F-269), a confidence gate that hid five months of returns (F-270), a column shipped ahead of its migration (F-271), a statement that arrived after the filing and was never re-compared (F-272), the owner-caught stub-pool verdict CN00184 (F-273), a half-running double-click and a puller that slept unnoticed (F-274), and the owner's law of order-dependence written as a rule and as code — the heal engine (F-275). Two the assistant's own. See the section at the foot of this file.

**v2.44, Session 205, 27 August 2026 — F-213 … F-217 appended. EVERY ONE FOUND BY MEASURING A RECORD AGAINST THE MACHINE IT DESCRIBES, none by a failure. Four of the five are the same shape: *a check that passes for a reason other than the one it names.* F-215 is the sharpest — the reinstall kit held the pre-fix bytes and its own `md5sum -c` was green, so a rebuild would have restored the 8h40m fault. Next free: **F-218**.**

**v2.43, Session 204 CLOSE, 27 August 2026 — F-207 … F-212 appended, THREE OF THE SIX THE ASSISTANT'S OWN.** The session that asked whether a pin is a backup. **F-209**: four live VPS files existed in ONE PLACE ONLY — including the clinic's money application — with `verify_live_pins.py` GREEN on every one of them, correctly, because *a hash is not a backup*. **F-208**: the audit convicted on re-keyed text and reported a drift that did not exist, dropping four lines in its own transcription — the precise thing `S181_postclose_addendum` §3 had already forbidden. **F-207**: a self-test that warns against a hardcoded ceiling literal sixteen lines above the hardcoded ceiling literal. **F-210**: the executable bit does not survive VPS → Windows → git, so a rebuild that verifies GREEN can still produce a backup script that never runs. **F-211**: the two document stores disagree in BOTH directions, one of the differences being a SIGNED policy shown as an unsigned draft. **F-212**: two publishers, one repo, no rule about which one publishes.

**v2.42, Session 203 CLOSE, 26 August 2026 — F-194 … F-206 appended, and AF-1's proposed strike REFUSED on measurement.** The session that looked at the machines themselves. Its spine is a **chain of three faults, each visible only because the one before it was fixed**: R2 gave the pull a log (18:38) → its first log ended `pipeline_status: post failed (HTTP Error 401)`, a line that had printed on every pull since S202 and been discarded every time (18:44) → traced to `_gate()`, which exempts three literal paths and was never told about `/finance/api/pipeline-status` (18:51). **B2 had never once reported.** Around it: the first medical-PC pins ever taken; the backup measured and the record found wrong; and sixty-nine Marg/medical documents collapsed to three under **D351**. **Five faults are recorded as the assistant's own, and a sixth was found at this close** — the AF-1 strike, refused because the fault it was said to be free of is live in the current bytes of `SEND_TO_CLINIC.bat` (`e19a8a77…`). §7 index F-193 → **F-206**; full text in the new §7.1 S203 section; next free **F-207**. §0–§6 unchanged — none of the thirteen is a surveillance fault code.**

**v2.41, Session 202 CLOSE, 26 August 2026 — F-187 … F-193 appended, and F-185 CORRECTED. SIX OF THE NINE FINDINGS THIS SESSION ARE THE ASSISTANT'S OWN**, and one is a correction of a claim it made and got wrong. The session's spine: an eight-hour silent outage of the pharmacy revenue feed, found only because the owner asked why a report had not arrived. **F-185 is CORRECTED, not deleted (F-23):** the assistant reported patient DIAGNOSES exposed in the public repo. **That was FALSE** — `.gitignore` had always excluded them and NOT ONE `.csv` is tracked; the scanner walked the filesystem instead of asking git what is public. Measured properly: 62 numbers, no diagnoses, ever. §7 index F-186 → **F-193**; next free **F-194**. §0–§6 unchanged.**

**v2.40, Session 202, 25 August 2026 — F-185 and F-186 appended, both found by MEASURING what a previous ruling had only estimated.** **F-185 is the serious one: the PUBLIC repository carries real patient data, including named patients with their DIAGNOSES.** F-96 (S181) recorded *"7 unmasked patient mobiles, ≥2 patient names and 1 clinic patient ID across 48 files"* and **D320 ruled, on that evidence, that the repo may stay public.** The first actual measurement, at the S202 open, found **133 distinct mobile-shaped numbers across ~190 files** — including two orphan sample files holding **13 named patients with age, sex, full mobile, diagnosis and comorbidities**, a script with 38 real caller numbers, and patient names paired with mobiles and clinic IDs inside `marg_report.py` selftest fixtures in three separate places. **The ruling was sound; the count it was given was wrong by roughly nineteen times, and had never looked at code or at test data.** **F-186:** `signatures.json` on manojz had drifted from its Register pin and nothing could see it — the live-pin discipline (F-97/D321) reaches only the VPS. §7 index F-184 → **F-186**; next free **F-187**. §0–§6 unchanged.**

**v2.39, Session 202, 25 August 2026 — F-184 appended at the S202 OPEN, the session it was reserved for, and CLOSED in the artefacts the same hour. It was reserved at the S201 close with one instance (the pin checker could only return AMBER because the close filed its canon into a per-close folder `verify_live_pins.py` never looks in). **Running README_VERIFY's own prescribed Phase-0 command at the S202 open found two more instances of the same root, and the third is the one that matters:** `MD5SUMS_ALL.txt` had not been rebuilt since the S197 fold, leaving **24 files present but unlisted**, and **twelve manifest-pinned canonical documents were absent from `KB_canon_all` altogether** — so the one mechanical command the README calls Phase 0 verification had been checking a SUBSET and reporting OK, never saying what it was not checking. `KIT_ID.txt`, whose only job is to carry that file's hash, disagreed with it and was nine sessions stale. All three folded into **F-184** rather than split — same folder, same routine, same root (the S191 fold precedent). Artefacts repaired at this open; the **routine fix — a numbered step that performs the inverse check — is OWED at the S202 close** as `END_OF_SESSION_PROMPT` v8. §7 index F-183 → **F-184**; full text in the new §7.1 S202 section; next free **F-185**. §0–§6 unchanged — F-184 is a record-keeping and install-integrity finding, not a surveillance fault code.**

**v2.38, Session 201, 25 August 2026 — F-179 … F-183 appended the session they were raised. THREE closed the same day by the kits that answer them (F-179 the outbox with no consumer · F-181 the nested `<a>` that broke a health row · F-182 `/finance/health` absent from the F-130 design table); F-180 closed by agent S201.11; F-183 OPEN by choice (two latent attribution faults deliberately left for their own kit). **Two housekeeping faults in THIS FILE corrected visibly, not silently:** the H1 read `v2.36` while the file was v2.37, and **F-178 was never given a §7 index row at the S200 close** — the F-45 and F-108 families, in the register that mints them. §7 index extended F-177 → **F-183** (F-178's missing row supplied); full text in the new §7.1 S201 section; next free **F-184**.**

**v2.37, Session 200, 25 August 2026 — F-178 appended the session it was raised (the mid-duty punch blindsight: first/last-only day computation makes a 4-hour mid-duty absence read as a full punctual day, and no page shows the sequence). OPEN — surfacing build queued. Next free F-179.**

**v2.36, Session 199, 24 August 2026 — F-174 … F-177 appended the session they were raised, ALL FOUR CLOSED the same day by the kits that answer them: the salary-engine exclusion-mirror drift (F-174, `S199_SALFIX`) · the unlabeled dress/I-card checkbox polarity with 88/74 phantom August fault-days (F-175, `S199_FLOW1` + migration) · the running day counted absent in month-to-date views (F-176, `S199_FLOW2`) · the scenario page's mislabeled months and missing leave component (F-177, `S199_SCEN3`). §7 index extended F-173 → F-177; full text in the new §7.1 S199 section; next free F-178.**
**v2.17, Session 181, 15 August 2026 — the three owed appends applied (F-82 … F-89). §0–§6 unchanged.**
**v2.30, Session 191, 19 August 2026 — the S190 candidates RULED and appended: **F-141** (a gate constant whose tail was composed from a narrative prefix — a value no file ever had — refused by the D317 gate with the box untouched; the delivery note's wrong install path folded in as the same fault's second instance), **F-142** (an installer's summary-reader took `tail -1` as the verdict and read a FAIL line as the summary — a harness that can misreport its own result), **F-143** (D331's quota counter summed the S155 migration rows, years of history DATED August 2026, so Darpan's line read "Rs 3,63,000 of Rs 15,000" and his legitimate ₹15,000 would have been refused — findable only on the box), **F-144** (the medical locked-day gate read the SSO broker role instead of the unit role and refused THE DOCTOR; the clinic twin had been correct since S182), **F-145** (an edited legacy day left the approvals queue while its money counted — a filter that hid a class did not un-hide a row that left it) and **F-146** (a refusal that looked like a save: the gate was right, the red went unseen, and "done" entered the session's belief state until the book proved absence — OPEN, rule adopted, UI fix owed). Raised at S190 and recorded-not-minted by design; ruled at S191. §0–§6 unchanged.**
**v2.29, Session 189 (expense menu), 18 August 2026 — **F-139** (the entry page's staff dropdown was hardcoded fiction — ids 1 and 2 pointing at a `staff_ref` table empty since S179 and never read or written by anything; surveyed before building: zero rows ever carried a staff_id, so the loaded gun was never fired; fixed in `S189_E1a`/`E1b` — the SERVER resolves the identity, the client's id is ignored) and **F-140** (kit E1a was refused by its own gate on the box: its selftest hunted a rehearsal day forward from 1 April into a D322 Sunday hole 135 days back, where the save answers `too_old` before the expense parse — the offline store was continuous, so the rehearsal never stood where the maker stands; reproduced offline on a gap-shaped copy to the exact six FAILs, fixed in `S189_E1b`). §0–§6 unchanged.**
**v2.28, Session 189 (build), 18 August 2026 — **F-137** (the record prescribed booking custody as cash movements and diagnosed a ₹2 lakh overstatement that never existed — the ledger subtracts every movement row, and the 17 Aug count proves the money never left the business; fixed by kits `S189_W1a`/`S189_W1b`/`S189_C1a`, custody recorded as location) and **F-138** (three of the four new F-137 checks asserted the store's absolute state and refused the very migration they were written to protect — after one neighbour had already been converted to a delta citing F-106; the C1a installer's honest red restored the books untouched; fixed in `S189_W1b`, which REPRODUCES the failure on a migrated copy before swapping). §0–§6 unchanged.**
**v2.27, Session 189, 18 August 2026 — **F-135** (a backlog instruction named three pages and two of them do not carry the thing it asked to assert — surveyed before building, so it never reached an installer) and **F-136** (the manifest keeps a copy of a staff-ledger md5 it says the Register owns; the Register moved on at S162 and nothing has checked the copy since, because a hash in the manifest but not the Register is checked by neither Phase 0 nor `verify_live_pins.py`). Both raised and appended the session they were found. §0–§6 unchanged.**
**v2.26, Session 188 FINAL, 18 August 2026 — **F-134**: the live-pin list is generated FROM the Register, so it must be regenerated at every close — and `END_OF_SESSION_PROMPT_v4` has **no step for it**. S187 did it by hand and wrote about it in the manifest; nothing carried the instruction forward, so the S188 close rebuilt the manifest and `MD5SUMS_ALL.txt` and **skipped the pin list**. The owner's close-out run of `verify_live_pins.py` therefore went **RED on two files the box had right**, from a list still built on Register **v5.22 (S187)** — three versions stale. The checker behaved perfectly: it refused to print VERIFIED, named `MANIFEST_MISMATCH`, and printed the pin it expected against the pin it had (the F-122 v1.2 fix). **The fault is the routine, not the tool.** Fixed by adding **step A8** — regenerate the pin list AFTER the manifest, because it depends on both. Next free **F-135**.**
**v2.25, Session 188 POST-CLOSE, 18 August 2026 — the close was published, the owner then opened Darpan's page as Darpan, and one look reopened it. **F-132** — the field labelled *"Opening cash · carried from the last filed day"* was `v_cash_ledger`'s running total over ALL history: the whole unit cash position, in 24px bold, and **not true of his drawer**. D2a had gated that route and recorded its payload as *"already correctly scoped"* — **a claim never tested, and wrong**; it leaked through the GET, the save response, and the mirror. **F-133** — asked to show what is parked with Dr Manoj and Dr Bhawna, the box was surveyed first, and the survey WAS the finding: `cash_movement` holds nothing but 15 bank deposits, `cash_custody_event` is empty, and **not one handover to either doctor has ever been recorded** though the entry has existed on that page since S179. Building it unsurveyed would have displayed a confident `₹0` against roughly two lakh. It also explains the drawer figure: the money left the room and never left the books. Kit `S188_D2c` live, 464/464 → **478/478**. Next free **F-134**.**
**v2.24, Session 188 CLOSE, 18 August 2026 — F-130 and F-131 appended at the close, both raised by ordinary work rather than by a failure. **F-130** — a page-only kit that preserves every element id is, by design, invisible to an id-based test, so the *design* of a page is the one thing 464 passing checks cannot see; found when a saved copy of the Hub could not be told apart from the live one by any gate we own. **F-131** — `git status` is not a read-only command: it refreshes the index, creating and deleting `.git/index.lock`, and on a mount that forbids deletes the lock survives and blocks every later write. **Fourteen occurrences across four sessions**, worked around by renaming the lock each time and never once recorded — so each session rediscovered it from scratch, and this one blocked a publish. Both fixes are specified and queued at the head of the S189 backlog. Next free **F-132**.**
**v2.23, Session 188, 18 August 2026 — F-127 … F-129 appended THE SAME SESSION they were raised, for the THIRD close running. Three findings from the Daily Flow v2 stage-D2 build: **F-127** — a role gate on the surface is not a role gate on the data; `_gate` protected the *unit* boundary but nothing protected the *role* boundary inside a unit, so `/finance/api/tile` handed the maker's browser the whole medical cash position on every page load. **F-128** — the offline rehearsal harness seeded a checker role for the smoke user, so eight "a maker cannot X" assertions had been passing by accident: the F-106 family living inside the thing that tests for the F-106 family. **F-129** — the D2 reveal marker recorded that a day had been shown, not *who* it had been shown to, so a checker's glance armed a badge against the maker. F-127 and F-129 were fixed and installed the same session (kits `S188_D2a`, `S188_D2b`); F-128 was fixed in the harness. §0–§6 and every prior finding unchanged; §7 index extended F-126 → F-129, full text in the new §7.1 S188 section. Next free **F-130**.**
**v2.22, Session 187, 18 August 2026 — F-122 … F-126 appended THE SAME SESSION they were raised, for the second close running. Five findings from the session that closed F-117 structurally and shipped eight kits: the generator's phantom manifest attestation (F-122, closed by `S187_V1a`), twin manifests in the repo (F-123, retired at this close), a publisher that printed success over a swallowed fatal (F-124, fixed same hour), a state-asserting test broken by the first real reception push (F-125, the fourth firing of the F-106 family), and an installer whose tail died on string-surgery quoting (F-126, now guarded by a whole-file `bash -n` rule). §0–§6 and every prior finding unchanged; §7 index extended F-121 → F-126, full text in the new §7.1 S187 section. Also corrected, visibly: §7's stale *"Next free finding: F-115"* line — it had not been advanced at v2.20/v2.21 while the index rows themselves were current (the F-45/F-108 family, caught by the §2-item-9 agreement check this register itself prescribes).**
**v2.21, Session 186 post-close, 17 August 2026 — F-115 … F-121 appended in one pass: the publish method that could not publish a close-out, and the five defects in the verification chain that the first RED pin run exposed. §0–§6 and every prior finding unchanged; §7 index extended F-114 → F-121, full text in the new §7.1 S186 POST-CLOSE section.**
**v2.19, Session 185, 17 August 2026 — the four owed appends applied in one pass: F-90 … F-95 (S181, never applied), F-100 … F-104 (S183), F-105 … F-106 (S184), F-107 … F-108 (S185). §7's index extended from F-89 to F-108; three new §7.1 continued sections carry the full text. Everything above the new §7 index rows and the new §7.1 blocks is byte-identical to v2.18, apart from this line, the H1, and the two CHANGELOG rows added at the head of the table (v2.19 and the reconstructed v2.18).**
>
> *(v2.18, Session 182, 16 August 2026 — F-96 … F-99 appended to §7.1; everything above that block was byte-identical to v2.17.)*

**Source of truth: `KB_Register` v5.2 (Tier 0 · what is true now) · `KB_History_Archive` v1.28 (Tier 1 · history) · `Diagnostics_Surveillance_System_Spec` v2.3 · `HANDOFF_RUNBOOK` v114 · `CANONICAL_MANIFEST.md`, which is authoritative on which version of each is current. The KB wins on any conflict.**

> *(Source-of-truth line CORRECTED at v2.17. It had read `Clinic_Master_KB_SystemsRegister_v1_58.md` · `Diagnostics_Surveillance_System_Spec_v2_0.md` · `HANDOFF_RUNBOOK_..._Session131_v69.md` — a monolithic KB that **no longer exists** (it split into Register + Archive at **D247**, S147), a Diagnostics spec three versions back, and a runbook forty-five versions back. This is the identical fault §0.2 point 1 raises against v1, recurring. See the v2.17 CHANGELOG row.)*

---

## §0 — WHAT THIS DOCUMENT IS, AND WHAT CHANGED

**This document is the single brain for RESPONSE.** Every fault → its lane → what the system does →
the exact procedure when a human is needed. **That is `D114`, and it stands.** It was considered for
retirement in Session 131 and **kept**: the Diagnostics Spec answers *"how do we detect it?"*; this
register answers *"what happens when it fires?"* They are not duplicates.

### §0.1 — The writer boundary (D203)

> **`Diagnostics_Surveillance_System_Spec` defines a fault code and how it is detected.**
> **This register assigns that code a lane and a procedure.**
> **A code is defined once, and laned once. Neither document restates the other.**

Where this register lists a code, it does so **to lane it**, never to redefine it. Where the
Diagnostics spec names a lane, it is quoting this register.

### §0.2 — Three things v1 said that were not true

*(This subsection is a Session-131 record. Its "current" figures are S131-era and are preserved
verbatim as history — the live source-of-truth line is the corrected one at the top of this file.)*

**1. Its source-of-truth line was twenty-five versions dead.** v1 cited *"Master KB v1.30 ·
Diagnostics Spec v1.4 · Runbook Session 62 (v42)."* Current: **KB v1.57 · Diagnostics v2.0 ·
Runbook v69.**

**2. Its front page and its body contradicted each other.** The header read *"THIS IS A DESIGN
DOCUMENT — nothing here is built or armed yet"* while §2.1 was titled *"S61 watchman, **LIVE**"* and
§2.3 *"Apps Script sentinel, **LIVE**"*. Both were partly right and the reader could not tell which:
**the detectors are live; the responder is not.** Every table below now carries that distinction
explicitly.

**3. F-24 — the register describes an auto-responder that does not exist.**
Nine faults in §2.1 are marked **AUTO→ESC**, *"System does: `systemctl restart call-api`; re-check;
alert."* But the live watchman (Diagnostics **§L2**) is, in its own words:

> *"**Read-only** — reports only; **never starts/stops/changes a service.**"*

It **names** the restart command inside an alert. It has never run one. And §M1's **D113** —
*"The S61 watchman **IS** the Lane-1 service responder"* — states a design intent as a fact. §4 of
this very document lists that responder as **Deliverable 2, unbuilt.**

> **This is not academic.** During an outage, a session reading v1's §2.1 would wait for a restart
> that never comes. **Every "System does" cell below is now marked with what actually happens today.**

### §0.3 — Codes detected but never laned

Session 125 built the `CALLHOOK_*` detector family. **Six of its codes have never appeared in this
register.** They are laned in **§2.5** below.

**And the two documents name the same fault differently:** Diagnostics §L2 registers
`VPS_SERVICE_DOWN` and `WATCHDOG_SELF_FAIL`; this register lanes nine per-service codes
(`VPS_CALL_RELAY_DOWN`, `VPS_WA_RELAY_DOWN`, …). **Both are correct and neither is wrong** — the
detector emits one code with the service name attached; this register lanes the response per service.
Recorded here so nobody "fixes" one to match the other.

---

## §0.35 — D204: THE RESPONDER DOES NOT EXIST, AND IS NOT SCHEDULED *(new in v2.1)*

**D204 (Session 132).** F-24 is answered. **D113 is an intent, not a fact.** The S61 watchman detects and
alerts; it prints `systemctl restart <svc>` inside the alert and **has never run one.** Deliverable 2 is
**unbuilt and unscheduled.** Per **D112**, promotion into Lane 1 is a logged decision, and **no fault has
earned one** — no service here has been observed dying unattended.

> **Every `AUTO→ESC` row below means, today: you are told, and a human restarts.**
> **During an outage, do not wait for a restart. Read the journal.**

The `System does` column throughout §2 is therefore to be read as **`System does — once Deliverable 2
exists`**. Its present tense is a label that misdescribes its contents (**D178**), and it stays only
because rewriting nine tables would risk the procedures they carry. **This paragraph is the label.**

---

## §0.4 — READ THE STATUS COLUMN BEFORE YOU TRUST A ROW

| Marker | Meaning |
|---|---|
| 🟢 **DETECTOR LIVE · RESPONDER LIVE** | The system detects it *and* acts. |
| 🟡 **DETECTOR LIVE · RESPONDER NOT BUILT** | You are told. **Nothing is done for you.** The "System does" cell describes Deliverable 2, which does not exist. |
| ⚪ **NEITHER BUILT** | Reserved. Detection not built. |

**As of Session 131, not one row is 🟢.** The Lane-1 auto-responder has never been built. Everything
live is **detect-and-alert**.

---

## 1. The two lanes (the whole safety model)

Every fault is assigned to exactly one lane.

### LANE 1 — NARROW-AUTO (system fixes it by itself)
The system detects the fault, runs a **proven-safe, idempotent** fix, re-checks, and reports
*"detected X → ran fix → confirmed healthy"* (or, if the fix didn't work, hands it to Lane 2).

**A fault qualifies for Lane 1 ONLY if its fix is:**
- **Idempotent** — safe to run twice with no harm, and
- **Proven harmless** — we have watched this exact action behave, and
- **Non-destructive** — it never deletes data, never touches PHI, never touches the MyOperator panel, never rotates a token.

**Starting Lane 1 deliberately TINY — only these two actions:**
| Action | Why it's safe |
|---|---|
| Restart a dead always-on service (`systemctl restart <svc>`) | systemd handles it cleanly; this is exactly what the S61 watchman already does, proven over weeks. |
| Re-run the follow-up push (`systemctl start clinic-followup-push.service`) | Replace-only / harmless — owner-confirmed it re-writes the same rows. |

Nothing else is Lane 1 until we deliberately **promote** it after watching it behave.
**Promoting a fault to Lane 1 is a decision, logged like any other.**

### LANE 2 — ASSISTED / STEPWISE (human-confirmed, session-driven)
For everything not in Lane 1, the system **never acts blindly**. It escalates to the doctor
(ntfy + Gmail) with the fault and a pointer to its procedure below. The doctor then handles
it **exactly like a coding session** — Claude presents one slice (fault → proposed action →
exact command), the doctor confirms, it runs, reports back, next slice. **No consequential
action ever runs without an explicit confirmation.**

> **How Lane 2 works in practice (Option 2a — agreed S63):** the background program only ever
> *detects and escalates* for Lane 2 — it takes no action itself. The stepwise "assistant"
> is Claude in a session, scripted by this register. This keeps the *acting-on-the-live-clinic*
> code surface as small as possible (just the two Lane-1 actions).

### The third response type inside Lane 2: AUTO-THEN-ESCALATE
Some faults get the Lane-1 fix **tried once**, and if the service does **not** recover, they
escalate to Lane 2 with the manual procedure. (This is already how the watchman behaves:
restart once → if still down, shout.) Marked below as **AUTO→ESC**.

---

---

> 🟡 **§2.1, §2.2, §2.3 — DETECTOR LIVE · RESPONDER NOT BUILT.** The watchman, the timer-freshness
> checker and the Apps Script sentinel all **detect and alert**. None of them restarts anything. Read
> every *"System does"* cell below as *"System **will** do, once Deliverable 2 is built."* Today the
> alert names the command and **you or Claude run it.**
>
> ⚪ **§2.4 — NEITHER BUILT**, except `WA_TOKEN_AGING` (still ESCALATE-ONLY, still overdue).

## 2. THE REGISTER — every current & reserved fault

Columns: **Fault code · Detected by · Lane · What the system does · If human needed: the procedure.**

### 2.1 Always-on service liveness (S61 watchman, LIVE)

| Fault code | Lane | System does | Procedure if it doesn't self-recover |
|---|---|---|---|
| `VPS_CALL_RELAY_DOWN` (:8097 dialer) | **AUTO→ESC** | `systemctl restart call-api`; re-check; alert | 1. `systemctl status call-api -l` + `journalctl -u call-api -n 80`. 2. If Python traceback → fix cause (build session), don't loop-restart. 3. Fallback: staff dial in MyOperator panel directly. Contact: Lokesh for panel. |
| `VPS_WA_RELAY_DOWN` (:8096 send) | **AUTO→ESC** | restart `wa-send-api`; re-check; alert | Same shape. Fallback: panel-native WhatsApp automations still fire independently. |
| `VPS_WA_RECEIVER_DOWN` (:8095 inbound) | **AUTO→ESC** | restart `wa-receiver`; re-check; alert | If it won't start: `journalctl -u wa-receiver -n 80`. Effect while down: WA_Inbox stops filling → dashboard WhatsApp feed empty. |
| `call-hook.service` down (:8098) | **AUTO→ESC** | restart `call-hook`; re-check; alert | While down: `Call_Durations` stops → duration gate can't unlock. Degrade-safe by design (won't retry-storm). |
| `clinic-portal.service` down (:8099) | **AUTO→ESC** | restart; re-check; alert | Staff launcher down; low urgency. Log check if repeats. |
| `clinic-followup-receiver` down (:8100) | **AUTO→ESC** | restart; re-check; alert | Catcher for the PC workbook. While down, the PC hook can't deliver — see follow-up faults. |
| `wa-notifier` down | **AUTO→ESC** | restart; re-check; alert | ntfy name-alerts stop; not patient-facing. |
| `attendance-dashboard` down (:8042) | **AUTO→ESC** | restart; re-check; alert | Attendance view down; staff record on paper; Secureye buffers punches. Non-clinical. |
| `attlistener` down | **AUTO→ESC** | restart; re-check; alert | Punches not recorded live; device buffers and syncs on recovery. |

### 2.2 Timer-job freshness (S62 checker, heartbeats LIVE, checker arms next)

| Fault code | Lane | System does | Procedure if human needed |
|---|---|---|---|
| `FOLLOWUPS_PUSH_MISSED_RUN` (CRITICAL) | **AUTO→ESC** | `systemctl start clinic-followup-push.service`; re-check heartbeat; alert | If heartbeat still stale after re-run → the **input** is missing. Check `clinic-followup-receiver` up + did Shavez run the Docterz export? Fallback: staff use last good list. |
| `RECORDING_ARCHIVE_MISSED_RUN` (WARNING) | **ASSISTED** | alert only — **NOT auto-run** | Overnight job; never confirmed harmless to run off-schedule. Stepwise: read `journalctl -u call-recording-archive -n 80` first → only then decide to `systemctl start` it. |
| `TRANSCRIPTION_MISSED_RUN` (WARNING) | **ASSISTED** | alert only — **NOT auto-run** | Same as above for `call-transcription`. Read log before acting. |

### 2.3 Follow-up list freshness (Apps Script sentinel, LIVE)

| Fault code | Lane | System does | Procedure if human needed |
|---|---|---|---|
| `FOLLOWUPS_LIST_STALE` / `FOLLOWUPS_NOT_LOADED` (CRITICAL) | **ASSISTED** | email you (sentinel) | 1. `cat /root/wa/heartbeats/followup-push.hb` — old? 2. Re-run push (safe). 3. Still empty → Docterz export missing (Shavez) or catcher down. |
| `FOLLOWUPS_DATE_MALFORMED` | **ASSISTED** | email you | Build-session fix — malformed due-dates in source; do not auto-touch data. |

### 2.4 Reserved / planned (in surveillance register; detection not all built yet)

| Fault code | Lane | System does | Procedure |
|---|---|---|---|
| `WA_TOKEN_AGING` (warn 80d → crit 90d) | **ESCALATE-ONLY** | alert only — **NEVER auto-acted** | Follow `SOP_WhatsApp_Token.md` exactly. HIGH RISK. Coordinate with Lokesh BEFORE rotating. |
| `PATIENT_MASTER_STALE` (WARNING) | **AUTO→ESC** | re-run `push_patient_mirror.py`; re-check | If still stale → source/service issue; read log. |
| `CALL_FEED_STALE` (WARNING) | **ASSISTED** | alert only | Known under-reporting (D61); investigate in build session. |
| `REVENUE_STALE` (WARNING) | **ASSISTED** | alert only | Reconciler live-state unconfirmed (see stub SOP). Verify before acting. |
| `DISK_SPACE_LOW` (planned maint. job) | **ESCALATE-ONLY** | alert only — **NEVER auto-delete** | Stepwise review of what's filling disk before removing anything. Deleting is never auto. |
| `LOG_ROTATION_OVERDUE` (planned maint. job) | **AUTO** (once built+proven) | prune per policy; report | Candidate for Lane-1 promotion *after* the prune is proven idempotent. Starts ASSISTED. |
| `BACKUP_MISSING` (planned maint. job) | **ESCALATE-ONLY** | alert only | A missing backup is never "fixed" automatically — you're told, you act. |

---


### 2.5 The `call-hook` 403 family (S125 detector LIVE · responder NOT BUILT) — **NEW in v2.0**

> These six codes were minted with the detector in Session 125 and **have never had a lane.**
> Detection: `Diagnostics_Surveillance_System_Spec_v2_0.md` **§L5**. Full incident:
> `INCIDENT_2026-07-08_CALLHOOK_403_v5_CONSOLIDATED.md`.

| Fault code | Lane | System does | Procedure if human needed |
|---|---|---|---|
| `CALLHOOK_SECRET_MISMATCH_403` (CRITICAL) | **ESCALATE-ONLY** | alert only — **NEVER auto-acted** | A secret mismatch is a key problem, not a service problem. **Never restart, never rotate automatically.** Read `INCIDENT_..._v5` §16 first. **Dual-key acceptance (D162) means a mismatch no longer causes an outage** — it means one key is stale. Coordinate with Lokesh before touching the MyOperator panel. |
| `CALLHOOK_MULTIPLE_KEYS` (WARNING) | **ESCALATE-ONLY** | alert only | More than one key seen in the access log. Expected *during* a rotation; unexpected otherwise. Check `rotate_callhook.sh status`. **The rotation is PARKED (S128).** |
| `CALLHOOK_403_EARLIER_TODAY` (WARNING) | **ASSISTED** | alert only | Deliveries were refused earlier today and are being accepted now. Read the access log before concluding it is healed. **D163's rejection logging exists precisely so this is visible.** |
| `CALLHOOK_NO_ACCEPTED_TODAY` (CRITICAL) | **ESCALATE-ONLY** | alert only | Zero accepted deliveries today. On a clinic day this is an outage. **`Call_Durations` stops → the duration gate cannot unlock → but it FAILS OPEN (D156), so staff can still file.** Diagnose; do not restart blindly. |
| `CALLHOOK_SILENT` (WARNING) | **ASSISTED** | alert only | No deliveries at all — accepted or refused. Distinguish *"no calls happened"* from *"the webhook is unplugged."* **Absence of coverage is not absence of events (§M5).** |
| `CALLHOOK_RAWLOG_MISSING` (WARNING) | **ASSISTED** | alert only | The raw `.jsonl` is missing. The receiver 403s **before** `raw_log()`, so a missing raw log and a refused delivery look identical from inside. Read the OpenLiteSpeed access log. |

**None of these is ever Lane 1.** A key, a panel, or a vendor is on the other end of every one of
them, and **rule 3 of §3 forbids the responder from touching any of the three.**


---

## 3. Rules that keep the responder sturdy (non-negotiable)

1. **One action per fault per outage.** Never restart-storm. Anti-spam state file, one alert
   per outage, recovery note on return. (Same DNA as watchman + checker.)
2. **Fail-loud.** If the responder itself errors, it shouts (ntfy+Gmail) — never dies silent.
3. **Read-only except the whitelisted Lane-1 actions.** The program's *only* write-actions are
   the exact `systemctl` commands in the Lane-1 list. It has no code path that deletes,
   edits data, touches PHI, or calls the MyOperator panel.
4. **Every alert names its procedure.** An alert is never just "X is down" — it carries the
   fault code, which maps here to the exact steps.
5. **Promotion is a logged decision.** Moving a fault ESCALATE→AUTO happens only after we've
   watched it behave, and is recorded as a D-decision.
6. **Log every action.** Plain log on the VPS; the daily report (deliverable 3) summarises it.

---

---

## 4. What gets built from this register (order)

- **Deliverable 2 — narrow auto-responder:** generalises the watchman's restart to the Lane-1
  list above (2 actions), AUTO→ESC behaviour for the service faults. Small, offline-tested,
  armed only with owner OK.
- **Deliverable 3 — maintenance jobs + daily health report:** the `DISK_SPACE_LOW`,
  `LOG_ROTATION_OVERDUE`, `BACKUP_MISSING`, `WA_TOKEN_AGING` detectors, plus a once-daily
  "everything healthy / here's what I auto-fixed today" summary to phone+email (so health is
  positively confirmed, not just silence-unless-broken).

---

---

## 5. Open questions for the owner (to resolve before building deliverable 2)
1. **Daily report timing** — what time should the once-a-day health summary land? (Suggest
   ~8 AM IST so it's the first thing you see, after the overnight jobs have run.)
2. **Report channel** — Gmail email, ntfy push, or both? (Suggest both: ntfy one-liner +
   Gmail with the detail.)
3. **Log-prune policy** — how many days of logs to keep before pruning? (Suggest 30 days;
   this decides whether `LOG_ROTATION_OVERDUE` can ever become Lane-1 AUTO.)


### §5.1 — Two of these three are now CLOSED (S131)

| | v1's question | Answer, from what shipped |
|---|---|---|
| **Q1** | Daily report timing? | **CLOSED — 09:00 IST.** `Health.gs` emails ✅/not-✅ every morning. Its *absence* is the fault. |
| **Q2** | Report channel? | **CLOSED — both.** `clinic_health_report.py` (Diagnostics §L4, D115): **ntfy one-liner + Gmail detail.** |
| **Q3** | Log-prune policy — how many days? | **STILL OPEN.** This decides whether `LOG_ROTATION_OVERDUE` can ever be promoted to Lane 1. The suggestion of 30 days stands and has never been ruled on. |

*v1 suggested ~8 AM. What shipped is 09:00 IST. The document was never told.*


---

## §6 — WHAT THIS REGISTER STILL OWES

- **Deliverable 2, the narrow auto-responder, has never been built.** Every `AUTO→ESC` and `AUTO` cell
  above is a promise, not a behaviour. **F-24.**
- **D113 must be re-stated or retired.** *"The S61 watchman IS the Lane-1 service responder"* is not
  true of the watchman that exists. It is either a design intent (say so) or a decision to build
  (schedule it).
- **Q3 — the log-prune policy** — is the last open question from S63.
- **The Maintenance & SOP project does not exist.** `SOP_WhatsApp_Token.md`, referenced under
  `WA_TOKEN_AGING`, has never been written. **A procedure that points at a document nobody wrote is
  not a procedure.**

---

## CHANGELOG

> **SEVEN rows below are marked 🔧 RECONSTRUCTED (v2.17, S181), and the seven are not all the same
> kind of gap.** **Six versions — v2.5, v2.7, v2.8, v2.13, v2.14 and v2.16 — each bumped this file and
> left no changelog entry at all**: the **F-45 family**, which this register minted at S149 for exactly
> this fault and which then recurred five more times, including at the version this one supersedes.
> **The seventh, v2.9, is a different case:** a row was present under that number but described
> Session 161, so it has moved to v2.7 where the evidence puts it, leaving v2.9 genuinely empty and
> reconstructed in turn. All seven are rebuilt from evidence, never from memory (**D172**), and each
> cites the artefact it was derived from. **A reconstructed row states what the version recorded, not
> the prose it would have used.** See the reconciliation note under the table.

| Version | Date | Change |
|---|---|---|
| **v2.43** | **27 Aug 2026 (Session 204, CLOSE — the session that asked whether a pin is a backup)** | **F-207 … F-212 appended the session they were raised — three of the six the assistant's own.** F-200 was answered at last (156 documents compared across both stores, in both directions), four live files were found to exist in one place only and three of them captured, the advance ceiling was made to agree across both systems under **D352**, and the assistant published for the first time — four commits, each verified against GitHub's HEAD rather than against the batch file's own output. No surveillance fault code, lane, procedure or rule was added or altered; §0–§6 unchanged. |
| **v2.42** | **26 Aug 2026 (Session 203, CLOSE — the session that looked at the machines themselves)** | **F-194 … F-206 appended; AF-1's proposed strike REFUSED.** **F-194** the B2 gate — `/finance/api/pipeline-status` was added at S202 and never added to `_gate()`'s three-path exemption, so every real post was refused before the route ran and **B2 had never once reported**; proven both ways on the box (401 `not_signed_in` before, HTTP 200 after) and then from the REAL caller at 19:10 and 19:17, not from a curl · **F-195** the reason it shipped: the smoke suite posts that route on a **signed-in** client, so the token clause was never exercised, and the check above it returned its 401 from the route rather than the gate — **both checks passed for reasons other than the ones they name**; and the +2 added at S203 to close this **do not bite** (reverting the gate still gives 721/721) — **OPEN**, recorded as green-and-meaningless · **F-196** `-- ok` written unconditionally and relayed to the clinic server as liveness · **F-197** the pull kept **no log at all** · **F-198** `marg_router.py` refused an unreadable `.xls` above the archive-and-index block, so it vanished and was re-refused every ten minutes for ever · **F-199** manojz's mirror is `robocopy /E` with **no `/PURGE`** — reasoning about the medical PC from it is unsafe · **F-200** **project knowledge was the stale store, not the repo**, and the four lines missing from its copy of the encryption note are exactly the warning that would have stopped a superseded finding being asserted as current — **OPEN** · **F-201** F-191(c) was wrong: the automatic backup was **never scheduled**, not configured-and-never-run · **F-202** the Marg token lives in **five** stores, not three — **OPEN**, rotation parked by the owner · **F-203** the runbook copy on manojz was the S201 version, missing the guest-access fault that caused the outage · **F-204** two assistant build-discipline faults: `py_compile` passed a `NameError` **twice** (anchor matched in two places; `pyflakes` adopted) and `trap … EXIT` pasted into an interactive shell left a reverted file on disk while it was believed restored · **F-205** **thirteen documents produced while consolidating sixty-nine away** · **F-206** AF-1 was carried as strikeable against a file that never held it, while its mechanism is intact in the live sender. §7 index F-193 → **F-206**; next free **F-207**. §0–§6 unchanged. Reverse-application-proven onto the `4883e3bd…` pin. |
| **v2.41** | **26 Aug 2026 (Session 202, CLOSE — the day the feed went dark, and six of the faults were ours)** | **F-187 … F-193 appended; F-185 CORRECTED.** The session opened on canon housekeeping and became an incident: **the Marg pull failed silently 23:08 → 07:33** while every component reported healthy — the medical PC on, the owner in an RDP session with it, Tailscale `active; direct`. The cause was Windows blocking unauthenticated guest access to the share. **Nothing was watching that leg, the error named the two innocent causes and not the guilty one, and a proven alternative route sat idle.** Around it: **F-187** the Rs 20,000 that left Darpan's drawer and existed only as prose, closed by PHYSICAL COUNT · **F-188** F-106 recurring · **F-189** GATES THAT DO NOT GATE (three assistant instances) · **F-190** `.gitattributes` never pinned `*.md`, leaving **192 of 208 canon files** free to change hash on a default Windows checkout · **F-191** MONITORS BORN DEAD (three, one eleven months old) · **F-192** a stale reading reported as a live state · **F-193** error messages naming the wrong cause (three in one day). §7 index F-186 → **F-193**; next free **F-194**. §0–§6 unchanged. |
| **v2.40** | **25 Aug 2026 (Session 202, open — the measurement pass)** | **F-185 · F-186 appended.** **F-185 — PATIENT DATA IN A PUBLIC REPOSITORY, and a ruling made on a count that was wrong by ~19×.** A pre-copy secret/PHI scan (run because a file was about to be copied INTO the repo) measured the repo for the first time: **133 distinct mobile-shaped numbers across ~190 files** against F-96's recorded *"7 mobiles, 2 names, 1 clinic patient ID across 48 files"*. Worse than the count: `plan-tool/test-data/patient_master.csv` and `patient_diagnosis.csv` held **13 named patients with age, sex, full mobile, DIAGNOSIS and comorbidities** — a data class F-96 never mentions because it only ever examined the canonical DOCUMENT set, never code and never test data. Also found: `recordings-archive/make_force_keys.py` (38 real caller numbers with dates and times) and patient names + mobiles + clinic IDs as `marg_report.py` selftest fixtures in **three** repo copies. **Acted on the same hour, and only where it was safe to:** the three orphan files — **referenced by nothing in the codebase**, verified by grep before moving — were **MOVED (never deleted)** to `D:\dr-manoj-git\_PHI_QUARANTINE_S202\` with a README stating plainly that moving them stops them travelling forward but does NOT remove them from past commits. **The live `marg_report.py` fixtures were deliberately NOT touched** — scrubbing only the repo copies would have created exactly the record-vs-reality drift F-186 is about. **NEW: `tools/phi_scan.py` + `PHI_SCAN.bat`**, the check that was missing, which never prints a matched value; its first run reports **271 files awaiting a first triage**, and that number is the finding, not a fault list. **RULE: a ruling inherits the reliability of the facts it was given — D172/D188 applied to a decision instead of a filename.** **F-185 stays OPEN pending the owner's re-ruling of D320.** **F-186 — the live-pin discipline stops at the VPS.** `margpull/signatures.json` on manojz read `3e9cbba0…` against a Register pin of `1b21f3bf…`, changed during S201 and never recorded. Diffed against the repo copy: **nothing removed**, four report types **gained an `end_marker`** (the row proving an export finished) each stamped *"S201: verified from a real sample"*, and one genuine new `STOCK_CLOSING` layout variant added. **The live file was strictly better than the record.** Record corrected FROM the box per the F-169 precedent, second provenance being the S201 stamps inside the file itself. `verify_live_pins.py` classifies this row BLIND and prints *"These are blind spots, not passes. Nothing here was verified"* — it was right to say so. **This is the concrete case for B2, and the second instance after the two-builds-stale medical parser.** §7 index F-184 → **F-186**; next free **F-187**. §0–§6 unchanged. |
| **v2.39** | **25 Aug 2026 (Session 202, OPEN — the housekeeping pass)** | **F-184 appended and CLOSED in the artefacts; the fault was three instances of one root — nothing numbered has ever owned `deploy_kits/KB_canon_all/`.** (i) The S200 and S201 closes filed their canon into per-close folders, so `verify_live_pins.py` — which looks in exactly ONE folder — could only ever return AMBER (`register_not_in_repo`): every pinned file matching, the source unprovable. This was the instance reserved at S201. (ii) `MD5SUMS_ALL.txt` was last rebuilt at the S197 fold; **24 files present in the folder were unlisted**, including every S198–S201 canon document, and the command exited with a WARNING on `CANONICAL_MANIFEST.md` — which **F-119 defines as a FAIL**. (iii) **Twelve manifest-pinned canonical documents were not in the folder at all**, living only inside per-close kits: `AUDITOR_SEED_v1`, `Clinic_Source_Data_Retention_Policy_v1`, `S195_Medical_Watcher_LIVE_Reference`, `START_HERE_SESSION_194/195/196`, `S198_Purchase_Portal_Design_CONTRACT`, `Fault_Action_Register_v2_37`, `HANDOFF_RUNBOOK_…v134`, `KB_History_Archive_v1_47_S200`, `START_HERE_SESSION_201`, `KB_Register_v5_21_S187`. **README_VERIFY.md states the contract in the folder's own words — *"EVERY manifest-pinned canonical row"* and *"files on disk = rows listed + those two"* — and names the inverse check as part of the close. No step performed it.** Repaired at this open: twelve documents filed (each verified against its manifest pin after the copy, not before), `MD5SUMS_ALL.txt` and `KIT_ID.txt` regenerated LAST, after every content change. **RULE: a folder that carries an integrity contract needs a step that executes it — a contract written in a README is a claim, not a check.** §7 index F-183 → **F-184**; next free **F-185**. §0–§6 unchanged. |
| **v2.38** | **25 Aug 2026 (Session 201, CLOSE — the Marg pipeline made whole)** | **F-179 … F-183 appended the session they were raised** — the outbox with no consumer (eleven verified reports undelivered while every component reported success) · the supervisor that could drift silently (answered by self-REPORTING, not self-updating) · the nested `<a>` that broke a row while both counting tests passed · `/finance/health` absent from the F-130 design table · and **F-183 OPEN by choice** (the backwards `0.60` tier + single-digit clinic IDs, left for their own kit). **Two faults in this file itself corrected visibly:** a stale H1 (`v2.36` at v2.37) and **F-178's missing §7 index row** — the F-45 and F-108 families recurring in the register that mints them. §7 index F-177 → **F-183**; next free **F-184**. Reverse-application-proven onto the `26bf427f…` pin. |
| **v2.37** | **25 Aug 2026 (Session 200, CLOSE — the go-live session)** | **F-178 appended, OPEN** — the mid-duty punch blindsight (every punch kept, only first/last used; no page shows the sequence). Surfacing + gap-flag build queued ⭐1; the selfie-GPS punch closes the no-punch remainder. Next free **F-179**. |
| **v2.36** | **24 Aug 2026 (Session 199, CLOSE — the salary-policy rebuild)** | **F-174 … F-177 appended the session they were raised, all four CLOSED same-day** — the exclusion-mirror drift (the D288 guard firing three sessions late and still preventing a mis-pay) · the unlabeled checkbox polarity (88/74 phantom August fault-days, migrated to 0 with backup) · today-counted-absent (owner-caught on the first preview) · the scenario's mislabeled months. §7 index F-173 → F-177; a new §7.1 S199 section; next free **F-178**. Reverse-application-proven onto the `8670b952…` pin. |
| **v2.35** | **23 Aug 2026 (Session 198, CLOSE — the eight-kit build day)** | **F-170 … F-173 appended the session they were raised.** **F-170** (an installer probe asserted an HTTP code never measured on the box — the live `S198_P1` v2 install rolled back healthy bytes because `127.0.0.1:8090` answers 301 to plain HTTP for old and new alike; v3 made probes informational and proved serving on the app's own render path; CLOSED) · **F-171** (the health page claimed worst-first ordering it never performed — docstring promised a sort that did not exist, live since S195, owner-found; CLOSED, kit `S198_H2`) · **F-172** (the Marg-push age check was Sunday-blind and cried "Something is wrong" on a fully-filed system; CLOSED, `S198_H2` — `_sundays_between`) · **F-173** (the April-2025 NEFT advice file's account column is SHIFTED against its names — possible wrong-account historical payments; **OPEN**, owner checks the April-2025 bank statement). Next free **F-174**. |
| **v2.34** | **23 Aug 2026 (Session 197, post-fold — the first pin run)** | **F-169 minted and CLOSED the same hour.** The owner's first `verify_live_pins.py` run on the S197-fold list went **RED on exactly one file**: `finance_entry.html` — record `bae2dd89…` (S190_F3), box `92477b06…`. **The box was right.** Kit `S193_UX` had patched the page in place and recorded the move in `S193_F6_Live_Pin_Record.md` — a doc the fold itself FILED to the repo — yet the fold's Register table carried the S190 value forward. The record was corrected FROM the box (F-118 precedent), the value confirmed against the S193 record — double provenance, nothing invented (Register v5.41 → v5.42; pin list regenerated). The checker chain (F-97 → D321 → F-110 → F-117 → F-122) caught it on its first opportunity. §7 index F-168 → **F-169**; next free **F-170**. §0–§6 unchanged. |
| **v2.33** | **23 Aug 2026 (Session 197, THE FOLD-IN — S193…S196 reconciled in one pass, the S185 precedent)** | **The F-series fork RECONCILED and FOURTEEN findings landed — F-155 … F-168.** The canon had been unfolded for four sessions (S193–S196 lived as standalone close docs), and the fork was exactly F-108's shape, live: this register said next-free F-155 while S193 had used F-155–F-159, S194 had recorded an "F-160 candidate", and S196 had written its candidates as F-160–F-162. **Resolution: every circulated number keeps its meaning** — F-155–F-159 S193's (all five CLOSED the session they were raised) · F-160–F-162 S196's (F-160 remedied same hour; F-161/F-162 closed by kits `S196_HLT2`/`S196_HLT3`) · S194's candidate minted **F-163** (closed same session) · S195's five unnumbered faults minted **F-164–F-168** (F-164–F-167 closed in-session or by standard; **F-168 OPEN** pending Drive-for-Desktop on the medical PC). Numbering deliberately non-chronological across F-160–F-168, recorded not silent. **F-148 and F-153 rows updated to CLOSED S193** (kit `S193_F6` — the drawer→ledger bridge live, seeded-store-first per F-87; `make_contra` stamps `against_month`). §7 index F-154 → **F-168**; full text in three new §7.1 sections; next free **F-169**. §0–§6 unchanged — none of the fourteen is a surveillance fault code. |
| **v2.32** | **19 Aug 2026 (Session 192, CLOSE)** | **FOUR findings CLOSED by shipping the code that answers them, and THREE minted.** CLOSED: **F-147** (the capacity rule — `S192_SL6`), **F-149** (the perks route — `S192_SL7`), **F-150** (policy dates as settings — `S192_SL5`), **F-151** (the prohibited word — `S192_SL5`). **F-148 stays OPEN**: `S192_F6` is designed and deliberately unbuilt, because `finance_app.py`'s smoke suite runs against a copy of the live store and cannot run offline — shipping into it on reasoning alone is **F-87** exactly. MINTED: **F-152** (`.gitattributes` never pinned `*.txt`/`*.md5` to LF — a CRLF `SUMS.md5` turns a good kit RED at its own gate; found from a publish warning, fixed same session), **F-153** (`make_contra` drops `against_month`, so a reversed advance keeps eating the month's quota — worked around, the one-line gap still open), **F-154** (the assistant had a live bridge to the owner's PC and did not use it; a delivery instruction even carried a literal `…/` placeholder the owner pasted as a path). §7 index F-151 → **F-154**; full text in the new §7.1 S192 section; next free **F-155**. §0–§6 unchanged — none of the seven is a surveillance fault code. |
| **v2.31** | **19 Aug 2026 (Session 191, CLOSE)** | **F-147 … F-151 appended the session they were raised — every one found by reading the LIVE system against its own signed rulings, none by a failure.** The owner asked one question — *"confirm the work done in the staff advances system"* — and the confirmation, done on the box rather than the record, surfaced five gaps between D250's judgment and the machine that implements its arithmetic: **F-147** the close records recovery the salary could not pay (D250's own "if salary can't bear all, the instalment skips" clause never built — the August close would have written ≈₹14,000 of repayment no money paid) · **F-148** the drawer→ledger bridge is unbuilt (`PENDING_LEDGER_WIRING`; B6 died when D330 superseded D329 whole, and nothing replaced it — every pharmacy-drawer advance reaches the salary book only by hand) · **F-149** the perks-recovery route is unreachable (D250: 3rd skip auto-flags recovery from perks; the machine hard-refuses instead) · **F-150** a policy start-date that lived only in session narrative was invisible to the machine that had to obey it (D249/D251: July "PREVIEW ONLY, policy starts August" — the live July salary applied both columns anyway, over-deducting ₹16,552.38 across twelve staff) · **F-151** the live system says "fine" in its column header and help text, the exact word D250's statutory caution prohibits. **All five ruled by the owner the same day** (build · build-and-test · correct · build-as-setting · correct) and folded into the signed **D332** contract — the Waiver, Defer & Repayment-Defined Advance layer — as kits S192_SL5/SL6/SL7/F6. All five OPEN pending those builds. §7 index extended F-146 → F-151; full text in the new §7.1 S191 section; next free **F-152**. §0–§6 unchanged. |
| **v2.30** | **19 Aug 2026 (Session 191)** | **The six S190 candidates ruled: five numbers, one fold — F-141 … F-146 appended.** They were raised during S190 and deliberately **recorded, not minted** (KB Register fold blocks, Archive §S190, Runbook v126 §2 ⭐2), because ruling on what earns a number is the owner's call; the register stayed v2.29 and said so, and nothing was owed. At S191 the owner ruled the call was the assistant's. **The fold:** the E2 delivery note's wrong install path is recorded **inside F-141** as its second instance rather than minted separately — same session, same root (a value written from narrative or memory with the record in reach), and splitting it would have made the F-109/F-116/F-135 family history less legible rather than more. **The five new rules:** a hash is transcribed from a measured value, never composed from a narrative prefix (F-141) · a harness must prove the line it read IS the summary (F-142) · a counter over dated rows must ask what the date MEANS (F-143) · with a broker in front of a unit, identity comes from the unit layer, and one wrong `u["role"]` licenses a sweep of all of them (F-144) · a queue that hides a class must un-hide a row the instant it leaves it (F-145). **F-146 is the only one left OPEN**: the discipline (verify in the book, not on the form) is adopted and standing, but the UI fix that would make a refusal impossible to mistake for a save is specified and unbuilt. §7 index extended F-140 → F-146; full text in the new §7.1 S190 section; next free advanced **F-141 → F-147**. §0–§6 unchanged. |
| **v2.29** | **18 Aug 2026 (Session 189, expense menu)** | **F-139 and F-140 appended the session they were raised — and both closed the same day, live (kit `S189_E1b`, smoke 488 → 509).** **F-139**: the expense form's staff selector offered `value="1" Darpan · value="2" Someone else` — ids into an empty table, "Someone else" a fake staff member — while `staff_ref` had never been read or written by the app since S179. Survey first (the F-133 habit): zero expense rows ever carried a staff_id, so no damage. Fixed: identity is SERVER-resolved (F-84's rule), the one real row created lazily, client ids ignored even from old cached pages. **F-140**: E1a's staged run went red at its own D317 gate — six checks, nothing swapped — because its rehearsal-day finder walked forward from 1 April into the store's first hole, a D322 Sunday 135 days back, beyond `BACKFILL_WINDOW_DAYS`; `too_old` fired before the expense parse the checks exist to test. The offline store was continuous: **right data, wrong shape.** Diagnosed by reproduction — a beyond-window gap yielded exactly the six box FAILs, a mid-window gap only three, which discriminated the hypotheses. Fixed: the finder runs backward from today (the D2/F-129 direction), and every check prints the server's error on failure. |
| **v2.28** | **18 Aug 2026 (Session 189 build)** | **F-137 and F-138 appended the session they were raised.** **F-137**: Runbook v124 ⭐0b and this register's own F-133 entry said cash in hand was *overstated by unbooked handovers*. It was not: `v_day_cash` computes `cash_out_p` from ALL of `cash_movement`, so booking the handovers as prescribed would have cut cash in hand from ₹2,05,198 to ≈₹30,000 — against a physical count (S186, 17 Aug) proving ₹1,75,198 genuinely held (owner ₹18,963 · Dr Bhawna ₹1,56,235). Owner ruling: that cash IS cash in hand, located elsewhere. Fixed: the card reads `cash_custody_event` (location, ledger-invisible) and kit `S189_C1a` recorded the counted position — ledger byte-identical, proven by the gate. **F-138**: C1a's first run was refused by three F-137 checks asserting absolutes ("parked must be ₹0.00") — the F-106/F-125 family, committed in the same session that had converted a neighbouring check to a delta for that exact reason. The installer restored the books; `S189_W1b` fixed the checks and its installer proves a count-equal kit by REPRODUCING the red on a migrated throwaway copy first. |
| **v2.27** | **18 Aug 2026 (Session 189)** | **F-135 and F-136 appended the session they were raised — fifth consecutive clean close.** **F-135**: the S188 close wrote a remediation instruction naming `approvals`, `workbench` and `review`; surveyed on the real bytes at S189, two of the three carry **none** of the four markers it asked to assert, because both predate Clinic Design Language v1. The instruction was a claim about three files and was written without opening two of them — **F-132's shape, in the record rather than the code**. Caught before it reached an installer; kit `S189_G1a` declares the measured truth in both directions instead. **F-136**: the manifest's Tier-2 Attendance row carries `staff_ledger.py v2.4 74dac84e…` while calling the value *Register-tracked*; Register v5.26 pins `92665b64…` and does not contain `74dac84e…` at all. Because the pin list is generated FROM the Register, `verify_live_pins.py` has never checked that hash, and the F-88 cross-check only asks whether a token is a document. **A hash in the manifest but not in the Register is checked by neither** — unverified since S162. |
| **v2.26** | **18 Aug 2026 (Session 188 final)** | **F-134 — the close-out routine had no step for the live-pin list, so the S188 close skipped it and the owner's own verification went RED on two files the box had right.** `live_pins.txt` is generated from the Register; S187 regenerated it by hand and recorded that fact as narrative in the manifest, but `END_OF_SESSION_PROMPT_v4` §A never gained a step, so nothing carried the instruction to the next close. The list was still built on Register v5.22, three versions stale. **`verify_live_pins.py` behaved perfectly** — refused VERIFIED, named `MANIFEST_MISMATCH`, printed expected-vs-actual (F-122 v1.2). Fixed by **step A8** (regenerate the pin list AFTER the manifest) and by regenerating it from v5.26. **§7 index extended F-133 → F-134; next-free advanced F-134 → F-135.** **Eight findings this session, every one appended the session it was raised.** No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged. |
| **v2.25** | **18 Aug 2026 (Session 188 POST-CLOSE)** | **The close was published; the owner opened Darpan's page as Darpan; one look reopened it.** **F-132** — the maker's page had been showing `v_cash_ledger`'s running total over all history under the label *"Opening cash · carried from the last filed day"*, and **D2a had recorded that route's payload as "already correctly scoped" without testing it**. Three doors leaked it: the GET, the save response, the mirror. Fixed and installed (`S188_D2c`, 464/464 → **478/478**). **F-133** — the request to display cash parked with the doctors was **surveyed before it was built**, and the survey was the finding: not one handover has ever been recorded, `cash_custody_event` is empty, and building it blind would have printed a confident `₹0` against two lakh. It also explains the drawer figure. Mitigated by rendering the zero as an instruction; the underlying overstatement of "cash in hand" **remains open**. **§7 index extended F-131 → F-133; full text in the new §7.1 S188 POST-CLOSE section; next-free advanced F-132 → F-134.** Seven findings this session, every one appended the session it was raised. No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged. |
| **v2.24** | **18 Aug 2026 (Session 188 close)** | **F-130 and F-131 appended at the close — five findings this session, all appended the session they were raised.** Neither of these came from a failure; both came from ordinary work noticing that a check did not cover what it appeared to. **F-130** — the design of a page is invisible to an id-based test, precisely because a page-only kit preserves every id on purpose; a saved copy of the Hub could not be distinguished from the live one by any gate we own, only by `md5sum` on the box. The remedy was already half-built (the S188 entry suite asserts a design fingerprint); three lines on each of the other three pages finish it. **F-131** — `git status` creates and deletes `.git/index.lock`, and on a mount that forbids deletes the lock survives and blocks every write. **Fourteen instances dated across S185–S188 were sitting in `.git/`, every one a silent workaround, none recorded** — the F-45 family in its purest form, and F-119's *a warning is a failure* applied to a person rather than a script. Fixed in practice by `--no-optional-locks`; the 14 files are owed a delete the bridge cannot perform. **§7 index extended F-129 → F-131; full text appended to the §7.1 S188 section; next-free advanced F-130 → F-132.** No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged. |
| **v2.23** | **18 Aug 2026 (Session 188)** | **F-127 … F-129 appended the same session they were raised — third consecutive close with no owed append.** Three findings from the stage-D2 build, and two of the three were found by *building the fix for the first one*. **F-127** — `/finance/api/tile` and `/finance/api/exceptions` carried no role check whatever; the unit gate made them look protected while the maker's page pulled the entire medical cash position on every load. The **F-84 family one layer in**. Fixed and installed the same session (`S188_D2a`). **F-128** — found only because F-127's fix *is* a role refusal and refused to go green: the offline seed granted the smoke user a checker role the live box does not have, so eight "a maker cannot X" assertions had been passing by accident for as long as the harness has existed. **The F-106 family inside the harness that tests for the F-106 family.** Correcting it moved the offline baseline 375 → 398 and is the reason the F-127 tests mean anything. **F-129** — the D2 reveal marker recorded the day, not the person, so a checker's glance armed the badge against the maker; a near relative of **F-118**, fixed and installed the same session (`S188_D2b`). **§7 index extended F-126 → F-129; full text in the new §7.1 S188 section; next-free advanced F-127 → F-130.** No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged — all three are access-scope, test-discipline and record-attribution findings. |
| **v2.22** | **18 Aug 2026 (Session 187)** | **F-122 … F-126 appended the same session they were raised — second consecutive close with no owed append.** Five findings: **F-122** (the generator attested to a transient whole-file manifest hash — a phantom minted at every generation — and the checker printed it as VERIFIED; closed structurally by `gen_live_pins.py`/`verify_live_pins.py` v1.2, kit `S187_V1a`: attest the stable CURRENT-row pin, prove it on the box), **F-123** (twin manifests — the `canonical-docs/` copy nine sessions stale yet self-describing as canonical; retired to the attic at this close, renamed, pointer left), **F-124** (`PUSH.bat` printed "pushed" over a swallowed `HEAD.lock` fatal; v2 verifies origin HEAD, and `PUBLISH_ALL.bat` — one whole-repo publisher with every gate — became the default method the same day, proven on its first field run), **F-125** (a state-asserting selftest went RED on the first real medical-PC push; the gate restored perfectly; check scoped to its own bytes and re-rehearsed against the failing condition — the fourth F-106-family firing), **F-126** (an installer tail syntax error after all real work; standing rule: `bash -n` the WHOLE installer before shipping). §7 index extended F-121 → **F-126**; new §7.1 S187 section carries full text; next-free advanced **F-122 → F-127**, and the stale "F-115" next-free line (unadvanced at v2.20/v2.21) corrected visibly. **F-108's agreement check was applied to this append.** No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged — all five are record-integrity, publishing and test-discipline findings. |
| **v2.20** | **17 Aug 2026 (Session 186)** | **F-109 … F-114 appended the same session they were raised — the first close since S181 that leaves this register with no owed append.** Six findings from one session: **F-109** (two characters of a hash invented at the previous fold-in), **F-110** (the live-pin checker held the box to a Register draft that never became canonical), **F-111** (the Register and its generator drifted apart because the generator was never re-run), **F-112** (a bank deposit that never happened, booked into the live books, on a row the record had itself marked unevidenced), **F-113** (a skip that was correct when made and expired unnoticed), **F-114** (a review queue holding lines no human could ever resolve). §7 index extended F-108 → **F-114**; a new §7.1 continued section carries the full text; next-free advanced **F-109 → F-115**. **F-108's own rule was applied to this append:** the next-free number and the last index row agree, and that agreement was checked. **No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged** — all six are process, record-integrity and reconciliation findings, not surveillance codes. |
| **v2.19** | **17 Aug 2026 (Session 185)** | **THE FOUR OWED APPENDS APPLIED IN ONE PASS — F-90 … F-108; the register is current again, and the gap that hid them is now a finding.** Applied: **F-90 … F-95** (S181 — *never applied to this register at all*), **F-100 … F-104** (S183, owed), **F-105 … F-106** (S184, owed), **F-107 … F-108** (S185, new). **§7 index extended from F-89 to F-108 (nineteen rows); §7.1 gains three continued sections** carrying full text for F-90–F-95, F-100–F-104 and F-105–F-108. Next-free advanced **F-90 → F-109**. **ONE version bump, not four:** this file has exactly one final state, and rewriting it three more times to simulate a version per session would be churn rather than provenance — every landed finding is itemised here and each carries its own session label. **F-108 minted from this register's own condition:** §7 read *"Next free finding: F-90"* while F-90–F-95 had never landed and F-96–F-99 sat in §7.1 with no index rows — **the F-45 family recurring**, after v2.17 had reconstructed six instances of it and named the pattern. The bodies for F-90–F-95 are **derived from evidence, never memory (D172)** — the KB Register v5.5 findings index, the v5.3 lineage row and Runbook v115/v117 — and state what the record held, not prose it never used. **No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged** — none of the nineteen is a surveillance code; they are process, security, install-integrity, reconciliation and record-keeping findings. |
| **v2.18** 🔧 | 16 Aug 2026 (Session 182) | *RECONSTRUCTED at v2.19.* **§7.1 extended — F-96, F-97, F-98 (CLOSED), F-99 recorded** as full-text blocks (the session that proved Phase 0 against git bytes and shipped the clinic portal tiles; full text also in KB History Archive §S182). **This bump left no CHANGELOG row of its own — the F-45 family, one version after v2.17 reconstructed six instances of it and named it.** It also added no §7 index rows for the four findings, which is half of **F-108**. No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged. *Derived from: this file's own §7.1 "(continued) — S182 · F-96 … F-99" section; KB Register v5.4 lineage row; CANONICAL_MANIFEST §S182 block pinning v2.18 at `ff0f020a3b645cbfa65400a51448cf0f`.* |
| **v2.17** | **15 Aug 2026 (Session 181)** | **THE THREE OWED APPENDS APPLIED — F-82 … F-89 merged; the register is current again.** This file had been carrying three unapplied appends for nine sessions, blocked from S180 only because the register itself was unreachable at Phase 0; it was **recovered by hash-search from the S171 cold kit** at the S180 close (md5 `1702b5a8e0663847eaa097919aea94d3`, matching its pin exactly) and all three could finally land. Merged: **F-82 + F-83** (owed since S172/S177), **F-84** (S179), **F-85 … F-89** (S180). **§7 index extended by eight rows; new §7.1 carries all eight findings' FULL TEXT verbatim** — the appends were full-text blocks, and §7's index-plus-Archive-pointer pattern would otherwise have discarded the text this register was handed. Next-free advanced **F-82 → F-90**. **SOURCE-OF-TRUTH LINE CORRECTED** (top of file): it had cited `Clinic_Master_KB_SystemsRegister_v1_58.md` — a monolith that **ceased to exist at D247/S147**, when the KB split into Register + Archive — plus Diagnostics v2.0 (now v2.3) and Runbook v69 (now v114). **This is §0.2 point 1's own fault, recurring**: v2.0 corrected a twenty-five-version-dead source line, and it went dead again by a restructure and forty-five runbook versions. §0.2 is preserved verbatim as the S131 record, so its "current" figures are historical, not live. **SEVEN CHANGELOG ROWS RECONSTRUCTED** — six that were never written (v2.5, v2.7, v2.8, v2.13, v2.14, v2.16 — the F-45 family recurring five times after this register minted it), plus v2.9, freed when a mislabelled row moved to the version the artefacts actually place it at. See the 🔧 rows and the reconciliation note below. **No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged** — not one of the eight new findings is a surveillance code; they are process, security, privacy, install-integrity and backup-discipline findings. |
| **v2.16** 🔧 | 12 Aug 2026 (Session 171) | *RECONSTRUCTED at v2.17.* **§7 extended — F-76 (WITHDRAWN), F-77, F-78, F-79, F-80 (all CLOSED) and F-81 (OPEN) recorded** (the session that finished the D297 console: acceptance sweep signed off, nine live installs across three files, D306–D308; full text KB History Archive §S171). No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged. *Derived from: KB Register findings index — "Full text: Fault Register v2.16 + Archive §S171"; the six F-rows themselves are present in §7 of this file carrying the S171 label.* |
| **v2.15** | **Session 170** | **§7 extended — F-75 recorded** (D297 console rev5 build-out session; full text KB History Archive §S170). No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged. |
| **v2.14** 🔧 | 11 Aug 2026 (Session 168) | *RECONSTRUCTED at v2.17.* **§7 extended — F-74 recorded** (D297 Stage B1 `/portal/console` page + Stage-2a agent backfill; full text KB History Archive §S168). No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged. *Derived from: KB Register findings index — "F-65–F-74 indexed in the v2.8–v2.14 Fault Registers / Archive §S162–§S168"; F-74 carries the S168 label in §7; Archive §S168 header confirms the date.* |
| **v2.13** 🔧 | 11 Aug 2026 (Session 167) | *RECONSTRUCTED at v2.17.* **§7 extended — F-72, F-73 recorded** (D297 Stage A console.db spine built; full text KB History Archive §S167). No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged. *Derived from: the same v2.8–v2.14 / §S162–§S168 span; F-72 and F-73 carry the S167 label in §7; Archive §S167 header confirms the date.* |
| **v2.12** | **Session 166** | **§7 extended — F-71 recorded** (D297 design/vetting session; full text KB History Archive §S166). F-71 = an uploaded follow-up-tracker zip carried PHI + `.secret_key`/`.env` (kin F-56); code-only read, nothing committed, rotation check owed. No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged. |
| **v2.11** | **Session 165** | **§7 extended — F-69, F-70 recorded** (D223 gist-tile build session; full text KB History Archive §S165). F-69 = `Call_Feed` dead since Apr (writer stopped); F-70 = Callback Tracker Core Dossier lags the live Sheet (diagnosis column + tab inventory). No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged. |
| **v2.10** | **Session 164** | **§7 extended — F-67 CLOSED, F-68 recorded** (salary coverage fix + pending-review board + Shivani maker + portal user admin session; full text KB History Archive §S164). F-67 fix shipped (coverage keys off `day_review` approved capture, D291); F-68 = same-origin-proxy pattern for cross-app widgets. No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged. |
| **v2.9** 🔧 | 10 Aug 2026 (Session 163) | *RECONSTRUCTED at v2.17.* **§7 extended — F-66, F-67 recorded** (D288 executed: standalone register salary proven to the rupee for July; register-owned EARLY-BIG rulings shipped; full text KB History Archive §S163). F-66 = WinSCP put the wrong bytes under a filename twice, caught by the md5 gate; F-67 = salary coverage keyed off the wrong table (latent under-deduction, fixed S164). No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged. *Derived from: the v2.8–v2.14 / §S162–§S168 span; F-66 and F-67 carry the S163 label in §7; Archive §S163 header confirms the date.* **See the reconciliation note below — a row previously carrying this version number described Session 161.** |
| **v2.8** 🔧 | 09 Aug 2026 (Session 162) | *RECONSTRUCTED at v2.17.* **§7 extended — F-65 recorded** (Stage-B salary APPROVE & LOCK; biometric grid; D288 consolidation directive; full text KB History Archive §S162). F-65 = a new SQLite table needs the app's `--init` **before** restart, or the page that queries it 500s. No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged. *Derived from: KB Register findings index — "F-65–F-74 indexed in the v2.8–v2.14 Fault Registers / Archive §S162–§S168"; F-65 carries the S162 label in §7; Archive §S162 header confirms the date.* |
| **v2.7** 🔧 | 09 Aug 2026 (Session 161) | *RECONSTRUCTED at v2.17.* **§7 extended — F-64 recorded** (Staff Register onboarding features + Salary Engine Stage A; the C-model salary policy locked, D272–D282; full text KB History Archive §S161). F-64 = `staff_ledger.py`'s code and data directories are different places; a same-named dir next to a module is not the module's location. No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged. *Derived from **two independent statements in Archive §S161**: its Phase 0 records the entering set as `Fault_Action_Register v2.6` (`6e90861e…`), and its F-64 entry ends "(Full text also in Fault Register **v2.7** §7)" — so S161 entered at v2.6 and closed at v2.7.* |
| **v2.6** | **Session 160** | **§7 extended — F-62, F-63 recorded** (Case Pack → VPS decision + portal health-tiles/layout session; full text KB History Archive §S160). No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged. |
| **v2.5** 🔧 | 08 Aug 2026 (Session 159) | *RECONSTRUCTED at v2.17.* **§7 extended — F-59, F-60, F-61 recorded** (portal Group D + personal tiles + GMB moved to the VPS; full text KB History Archive §S159). F-59 = Chrome refuses ports 5060/5061 as ERR_UNSAFE_PORT; F-60 = the VPS filesystem is case-sensitive; F-61 = a pasted fence label broke `portal_config.py`. No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged. *Derived from: KB Register findings index — "Full text of all three: Fault Register **v2.5** + Archive §S159"; all three carry the S159 label in §7; date from the KB Register version-lineage row v3.2 · S159 · 08 Aug 2026.* |
| **v2.4** | **Session 158** | **§7 extended — F-57, F-58 recorded** (SSO-portal build + Notion catch-up session; full text in KB History Archive §S158). No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged. |
| **v2.3** | **Session 157** | **§7 extended — F-54, F-55, F-56 recorded** (documentation/design session; full text in KB History Archive §S157). Title line corrected v2.1→v2.3 (it had lagged behind the v2.2 body — the F-45 title-lag family). No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged. |
| **v2.2** | **Session 156** | **§7 added — a Later-Findings index (F-45..F-53)** so the register is aware of the process/build findings minted from S149 on (full text lives in the KB History Archive per that era's pattern). **F-51/F-52/F-53 recorded** (S156). No surveillance fault code, lane, procedure or rule was added or altered; §0–§6 are unchanged from v2.1. |
| **v2.1** | **Session 132** *(row backfilled S149 per F-45; the v2.1 bump left no changelog entry — the same stale-record family caught at v1.71/§S131/§S143. Day not re-derived from the artefact; session is verified: D204 = S132)* | **§0.35 added — D204 (Session 132): F-24 is answered.** The Lane-1 auto-responder **does not exist and is not scheduled**; **D113** ("the S61 watchman IS the Lane-1 responder") is reclassified as **intent, not fact**. The watchman prints `systemctl restart <svc>` inside its alerts but **has never run one** — Deliverable 2 is unbuilt, and per **D112** no fault has earned Lane-1 promotion. So every `AUTO→ESC` row reads, today: *you are told, and a human restarts; during an outage do not wait for a restart — read the journal.* The `System does` column is relabelled **"System does — once Deliverable 2 exists"** (**D178**: its present tense misdescribes its contents). **No lane, procedure or rule was altered; §1–§6 are unchanged from v2.0.** |
| **v2.0** | **09 Jul 2026 (Session 131)** | **RE-BASED, self-contained, status-true.** **Not retired** — `D114` makes this the single brain for response, and Session 131 confirmed it after nearly retiring it without reading D114. **D203** states the writer boundary: Diagnostics *defines and detects* a fault code; this register *lanes* it; neither restates the other. **F-24 raised:** v1's §2.1 described an auto-responder (`systemctl restart …`) that **does not exist** — the live watchman is read-only and *"never starts/stops/changes a service."* Every table now carries a status marker; **not one row is 🟢.** Source-of-truth line corrected (was KB v1.30 · Diagnostics v1.4 · Runbook v42 — twenty-five versions dead). **§2.5 added:** the six `CALLHOOK_*` codes, detected since Session 125 and never laned. §5's Q1 and Q2 **closed** by what shipped (09:00 IST; ntfy + Gmail). **§1, §2.1–§2.4, §3, §4 and §5 are reproduced verbatim; no rule, lane or procedure was altered.** |
| v1 | 04 Jul 2026 (Session 63) | First draft. Two lanes, the register, the six sturdiness rules, the build order, three open questions. Its header said *"nothing here is built or armed yet"* while its body marked three detectors LIVE. |

### CHANGELOG reconciliation note (v2.17, S181) — one conflict, left visible

**The row that used to read `v2.9 | Session 161 | F-64` was carrying the wrong version number, and
its content now sits at v2.7.** Two independent statements inside **Archive §S161** — a session
narrative written at that close, not from memory — establish it:

1. §S161's Phase 0 records the **entering** canonical set as `Fault_Action_Register` **v2.6**
   (`6e90861e…`). A session that enters at v2.6 cannot close at v2.9 without two silent extra bumps.
2. §S161's F-64 entry ends: *"(Full text also in Fault Register **v2.7** §7.)"*

Against that, the only evidence for "v2.9 = S161" was the changelog label itself. **A label is not
provenance (D188), and a check's expected value is derived from the artefact, never predicted from
memory of it (D172)** — so the artefact wins, the row moved to v2.7, and the genuine v2.9 (Session
163, F-66 + F-67) has been reconstructed into the gap it left.

**What is NOT claimed here.** The reconstructed rows state *which findings each version recorded* and
*what session and date it belonged to*, because those are evidenced. They do **not** reproduce the
prose those rows would have carried — that text was never written and is not recoverable. **The
correct entry is sometimes UNKNOWN (D166)**, and where a row says only "§7 extended — F-## recorded",
that is the whole of what the evidence supports.

**No F-number was spent on this.** The recurrence of the F-45 family across six versions is recorded
here and flagged to the owner; minting it as a finding remains the owner's call. Next free finding
stays **F-90**.

---

## §7 — LATER FINDINGS INDEX (F-45+, recorded in full in the KB History Archive)

Findings from S149 onward are minted and described in full in their session's Archive `§S###` block; this index keeps the register aware of them. They are process/build/discipline findings, not new surveillance fault codes, so they add no lane or detector here.

**From F-82 onward the full text also lives in this file, at §7.1** — those findings arrived as
standalone append blocks and the text is carried rather than discarded.

| F-## | Session | One line | Full text |
|---|---|---|---|
| F-45 | S149 | Fault-Register v2.1 bump left no CHANGELOG row (stale-record family) — backfilled | Archive §S149 |
| F-46 | S151 | Salary column printed in-chat (header-keyed mask beaten by a title row) → whitelist-only mask rule | Archive §S151 |
| F-47 | S153 | Double-punch artefact: arrival double-punch, no out-punch — classify pairs before money math | Archive §S153 |
| F-48 | S153 | Shadow-write / diff-audit rule for owner-side workbook edits | Archive §S153 |
| F-49 | S154→S155 | Salary CSV in the git working tree → blanket `*.csv` gitignore IS the gate (CLOSED by ruling S155) | Archive §S154/§S155 |
| F-50 | S155 | Derived-everything role powers (`list(CATEGORIES.keys())`) → **a role's powers are an explicit allow-list**; every power-set gets a negative selftest | Archive §S155 |
| **F-51** | **S156** | One-tap irreversible ledger appends (contra/skip) → confirm step + void-pair display; **fixed same session** | Archive §S156 |
| **F-52** | **S156** | Repo copy of a live op-script silently stale vs the VPS (gutlog missing) — **build from the md5-verified live copy, never the repo mirror** (reinforces D160) | Archive §S156 |
| **F-53** | **S156** | Compile/selftest on a NEWER Python than the deployment target proves nothing — **VPS-Python (3.11) compile + selftest mandatory before delivery** | Archive §S156 |
| **F-54** | **S157** | `App_Service_Register_v1` carried a 07-Aug file date over **Session-63-era** content (missing the asset app, staff-ledger, the salary stack) — a "date/filename is not provenance" trap (D188); reconcile against the live KB/manifest, not the artefact that looks current | Archive §S157 |
| **F-55** | **S157** | The `drmanoj-clinic-automation` **GitHub JSON repo-dump is partial** — the export tool truncated (binary `attendance.zip` ate the budget), silently omitting `staff_ledger`, `wa-diagnostics`, `revenue-reconciliation`, `plan-tool`; use the **live repo** (codeload tarball / raw), never a dump assumed complete | Archive §S157 |
| **F-56** | **S157** | Uploaded PC "code" zips carried **live credentials (GCP service-account key, `.env`, `.secret_key`) + PHI + F-31 salary data** even after "most data files" were deleted → sanitize whole `data/`/`output/`/archive dirs + keys before aggregating anything for reuse; **the service-account key that rode through must be ROTATED** | Archive §S157 |
| **F-57** | **S158** | Notion catch-up scope taken from OUR records (claimed S150) not the live target (actually S147) — the real gap was S148–S156. **Scope a catch-up from where the external system actually is**, not from where we think we left it (reinforces D188/D260). (The 7-session "Notion absent" streak also had a mechanical cause: connector toggled OFF per-chat.) | Archive §S158 |
| **F-62** | **S160** | “Audit the artefact, not the label” — a doc filed **Surgical Case Pack** as “Website/SEO”, hiding that it is a **local PHI store** (case bundles+consents+ledger, off-Drive by design). Classify a component from its CODE/data-flow, not a doc's category tag (kin D188/F-54). | Archive §S160 |
| **F-63** | **S160** | The portal **`pc`-NameError reached production** — `py_compile` + an isolated Jinja render both passed, but the **wired route was never exercised** (the name existed only as a render kwarg). DELIVERY GATE for any live Flask change: a **test-client hit on the ACTUAL route** (200 + expected content), not just compile + isolated render. | Archive §S160 |
| **F-64** | **S161** | Reusing live code from another app: `staff_ledger.py` **code** lives at `/root/staff_ledger.py` while its **data** dir is the separate `/root/staff_ledger/` — importing the ledger's `compute_salary` from the register app required adding `/root` **and** `/root/portal` to `sys.path` (guarded). A same-named dir next to a module is not the module's location; put the module's parent on the path. Diagnosed via a `ModuleNotFoundError` surfaced by a temporary error-carrying module global. | Archive §S161 |
| **F-58** | **S158** | Flask's **test client ignores a manually-set `Cookie` header** (it manages its own cookie jar) — a valid SSO token gave a false-negative auth until switched to the client's `set_cookie` jar. Smoke-test cookie auth via `set_cookie`/`test_request_context`, never a raw header. | Archive §S158 |

| **F-59** | **S159** | Chrome refuses ports **5060/5061 (SIP)** as **ERR_UNSAFE_PORT** from every context (address bar or tile); `curl`/CLI ignore the restricted-port list, so the server looks healthy while the browser fails. Avoid Chrome's restricted ports for localhost tiles; when curl works but the browser won't open, suspect ERR_UNSAFE_PORT first. | Archive §S159 |
| **F-60** | **S159** | VPS filesystem is **case-sensitive**: `GMB.html` ≠ `gmb.html` — a path-based read fails with the app's own "not installed" message though the file is present. The filename's case must match what the code opens (kin of D188). | Archive §S159 |
| **F-61** | **S159** | Pasting a fenced code block's **language label** (```` ```python ````) into a live config put a bare `python` token in `portal_config.py` → `NameError` → whole config unreadable → portal "Setup needed" (secrets intact). Paste only lines BETWEEN the fences; diagnose a sudden "unconfigured" via `python -c "import portal_config"`. | Archive §S159 |

| **F-65** | **S162** | A new SQLite table needs the app's `--init` (migration) run **BEFORE** `systemctl restart`, or the page that queries it 500s. The Stage-B lock page queries `locked_run`; installing the code without `--init` → table missing → 500. Standing rule: when a delivery adds/alters a table, run `--init` before restart AND md5-check the file so a truncated/placeholder copy is caught. (First miss's root cause: a literal `PYBIN` placeholder in the runbook meant the venv `--init` never ran — always paste the real `/root/wa/venv/bin/python3`, never a placeholder.) | Archive §S162 |
| **F-66** | **S163** | **WinSCP silently put the WRONG bytes under a filename — twice** — during the S163 install: the "salary engine" was uploaded but the local save was actually `staff_register.py`, so `salary_engine.py` on the VPS held the register file (`md5 = ded3ae8f…`, the register's hash) though its name looked right; a later `mv`/upload shuffle also **deleted the live `staff_register.py`** (service went to `activating`/down). The **md5 gate caught the wrong bytes before any restart**, and both files were restored from the `.bak-S163eb` timestamped backups — no mis-paid run, contained downtime. Standing discipline reinforced: (a) **always keep a timestamped backup before install** (`cp file{,.bak-SNNN}`), it is the instant rollback; (b) **upload with a `.new` suffix, md5-verify the file IN PLACE, then `mv` into position** — never overwrite a live file with unverified bytes; (c) a filename is not provenance (D188) — trust only the hash. | Archive §S163 |
| **F-67** | **S163** | **Coverage detection keys off the wrong table.** `salary_engine.load_register()` sets `covered = (daily_register rowcount > 0)`, but `daily_register` only holds EXCEPTION rows — a month the register genuinely captured (day_review approved daily) but with zero logged exceptions would be mis-flagged **uncovered**, skipping the C-model base÷30 cuts on genuine absences (an under-deduction). The correct signal is **day_review capture** for the month, not exception rows. Latent (August is currently uncovered for a legitimate reason — no daily entry yet), but MUST be fixed before any register-captured month is paid. Fix + selftest were the S164 top task. **CLOSED S164 (D291):** `covered` now keys off `day_review` `status='approved'` capture (not exception rows); `salary_engine.py 5514918067243e3f39e7074144ee7db4`, selftest **CASE E** added, July parity re-verified ₹1,07,447. | Archive §S163/§S164 |

| **F-68** | **S164** | **Cross-origin credentialed fetch through OpenLiteSpeed is fragile.** The portal Staff-Register tile fetched the register's `/register/review/counts` from the browser and got nothing — OLS's reverse proxy strips/omits the `Origin`/CORS headers a credentialed cross-origin `fetch` needs, so the browser blocks the response. Pattern: don't fetch another app's origin from the browser — add a **same-origin proxy** on the calling app that server-side calls the target over localhost (here portal `GET /portal/review-counts` → `REGISTER_COUNTS_URL` = `127.0.0.1:8044/register/review/counts`, SSO cookie forwarded, 2s timeout, empty `{}` on failure). Apply to any future cross-app widget. | Archive §S164 |

| **F-69** | **S165** | **`Call_Feed` dead since 28 Apr 2026.** While binding the gist's call-volume source, `Call_Feed` (the name-free feed the Follow-Up Tracker reads; written by `CallField`/`CallFeed.gs`) was found frozen at April — 2,971 rows, newest 27–28 Apr, **0 today** — its writer stopped ~3.5 months ago. Volume was rebound to the live `Call_Durations` (1,648 rows, 79 today; `category` incoming/obd, window `ended_at_ist`, probe excluded). The Follow-Up Tracker reads `Call_Feed`, so its incoming/outgoing reconciliation is likely silently degraded since April — find and restart the `Call_Feed` writer. | Archive §S165 |
| **F-70** | **S165** | **The Callback Tracker Core Dossier lags the live Sheet (doc-not-provenance, D160/D188).** The dossier frames diagnosis as Docterz-side, but `Patient_Master` carries a live **Diagnosis** column (present for most patients) and `Followups_Today`/`Followup_Escalations` carry it too — the console's diagnosis column is buildable now, not Docterz-blocked. The dossier also lacks the real tab inventory (there is **no** "Escalations" tab; 3rd-strikes live in `K_Strikes.Tries`; the Sheet has 19 tabs incl. `Daily_Summary`, `Agents`, `Followup_Outcomes`). Owner corrected the assistant from the live Sheet. Dossier update owed. | Archive §S165 |

| **F-71** | **S166** | **An uploaded PC zip carried PHI + secrets (kin F-56).** The `followup_tracker.zip` shared to ground the D297 conversion/no-show design included `patient_master.csv`, `patient_diagnosis.csv` (PHI), revenue ledgers, and `.secret_key` + `.env` (secrets). Handled correctly: **code-only** extraction, **nothing committed** to any repo or kit, **no data printed** (numbers masked in chat). Standing rule reinforced: PC uploads must be **code-only** (drop `data/`). **Action:** treat the shared `.secret_key`/`.env` as potentially exposed → rotation check (kin F-56 service-account-key rotation). | Archive §S166 |

| **F-72** | **S167** | **Mixed tz-aware/naive datetime subtraction crashed the console builder.** `portal_console.py`'s first live dry-run died in `build_latency` — `TypeError: can't subtract offset-naive and offset-aware datetimes`: one timestamp column parses tz-aware (an ISO string carrying `+05:30`), another naive, and subtracting the two raises. Fix: `parse_ts` strips `tzinfo` so every parsed time is one **naive IST wall clock** (all sources are IST); a genuine cross-zone source would then surface as a ~constant offset in the latency stats, not a silent wrong lag (F-41 lineage). RULE: normalise datetimes to one tz stance before arithmetic; unit-test with an aware+naive mix. | Archive §S167 |
| **F-73** | **S167** | **Two live files disagreed on the MyOperator `/search` `status` vocabulary.** `Netting.gs`/`MyOperator.gs` (which produce `Daily_Summary`) read `status` as **numeric** (`status==2`=missed); the VPS sibling `flag_investigator.py` reads it as **strings** (`"missed"/"voicemail"/"bridged"`). Encoding the A2b reconcile on the wrong one would silently mis-count net-missed. Resolved by a **read-only live probe** (`--myop-probe`): the API returns numeric `status` `{1,2}` + `event` `{1,2}` — **numeric wins**; `Netting.gs` is authoritative. RULE: when two live sources disagree on a field's encoding, PROBE the live source before encoding a rule — do not pick by the file's recency or apparent authority (kin D160/D188). | Archive §S167 |

| **F-74** | **S168** | **Console call-count inflation from a one-to-many LEFT JOIN fan-out.** The first `/portal/console` render showed impossible totals (Incoming **2276** > all-calls **1651**): `LEFT JOIN verdicts` multiplied each call row by its verdict count (a re-judged call carries several — **2195** verdicts across **1651** calls), and `LEFT JOIN patients` compounded it. Fix: collapse each child to **one row per key BEFORE joining** — dedup subqueries `_DV` (verdicts: `MAX(id)` per `join_key` → newest wins) + `_DP` (patients per `phone10`); counts then reconcile (each dimension sums to the spine total). Caught in the browser at first build — nothing downstream had consumed the wrong numbers, so no incident. RULE: never `LEFT JOIN` a one-to-many child straight into a counted spine — reduce it to one-row-per-key first, and sanity-check that a dimension's parts sum to the spine. | Archive §S168 |
| **F-75** | **S170** | **`portal_console.py --build` is WINDOW-SCOPED and ATOMIC-FROM-SCRATCH — a small `--days` scheduled run silently destroys the wide-window layers every fire.** Observed at the Item-1 cron gate: a dry-verify `--days 3` run rebuilt `console.db` whole and shrank `call_agent` **1001 → 60** and reverted net-missed-open **108 → 152** — the Stage-2a attribution and the MyOperator correction only ever cover the pulled window, and there is NO incremental mode. Had the punch-list's assumed light cron been armed blind, the console would have shredded its own back-catalogue every 10 minutes while *looking* fresh. Caught because the gate ran the exact scheduled command once by hand and compared artefacts before arming (the F-41 instrument, applied forward). FIX (D303): the scheduled job is ALWAYS the full `--days 60 --with-myop-reconcile --with-transcripts` build (~32 s) under a mandatory `flock -n`. RULE: before arming any schedule, run its exact command once and diff the artefact's key invariants (row counts, watermarks) against the pre-state — a fresh timestamp alone proves nothing about what the run preserved. | Archive §S170 |

| **F-76** | **S171 · WITHDRAWN** | Builder's Google SA is read-only → `Dr_Manoj_Call_List` sheet write 403 (caught by the acceptance sweep — offline selftests never exercised the live write scope: a check that cannot fail is not a check). WITHDRAWN by **D306**: the scope is NOT widened; `console_reviews.db` on the VPS is canonical, the sheet push is removed as dead code, Drive becomes nightly-backup-only. | Archive §S171 |
| **F-77** | **S171 · CLOSED** | The training CSV `/portal/console/reviews.csv` downloaded empty / Excel-hostile; fixed with a **UTF-8 BOM** + route hardening, re-verified live. | Archive §S171 |
| **F-78** | **S171 · CLOSED** | `build_no_shows` sliced the feed's `DD-Mon-YYYY` due date with `[:10]` — a correctness bug wearing a cosmetic face: the due-vs-today lexical gate AND the calls-since-due SQL boundary were computed against the wrong format (columns unreliable, not just a chopped year). Fix: parse to ISO at build; format for humans only at display. RULE: never slice a date string by length — parse it. | Archive §S171 |
| **F-79** | **S171 · CLOSED** | A stale `details.callrow>summary{…flex…}` rule sat LATER in the stylesheet than the new grid rule — rows silently fell back to flex while headers rendered grid (the "headers don't match rows" defect). **CSS cascade regressions are invisible to string-assertion gates.** Cure: DELETE the stale rule (not out-specificity it) + the F-63 gate now asserts on the SERVED HTML, including the ABSENCE of known-stale rules (**D307c**). | Archive §S171 |
| **F-80** | **S171 · CLOSED** | gspread **6.x** `Spreadsheet.client` returns an HTTPClient WITHOUT `open_by_key`; the resulting AttributeError was swallowed by a broad except → patient enrichment reported `found=False` forever while looking like a share problem. Fix: open the enrich sheet via the base `gc` client inside `_open_clients`. RULE: never let a version-sensitive attribute path fail silently — fail loud or probe it (kin F-73). | Archive §S171 |
| **F-81** | **S171 · OPEN** | **Duplicate call rows in the live log** — same phone/time/duration appearing twice (e.g. 16:51:55 ×2, 16:50:19 ×2). Suspected MyOperator `/search` reconcile double-insert in the builder. Displayed honestly, not hidden (D236). **Builder-side investigation owed** (dedupe on a natural key or prove two genuine legs). | Archive §S171 |

| **F-82** | **S172 · OPEN (VENDOR)** | MyOperator WhatsApp Developer API returns **HTTP 500 `{"message":null}` on ALL authenticated calls** — reads and sends alike, from two independent code paths on the identical token. An unauthenticated call correctly returns 401, so the API is up and the token passes the auth gate; only **account resolution** fails → vendor-side provisioning. **WABA go-live blocked.** Escalated to Khushi + Lokesh; `PORTAL_WA_DRYRUN` returned to `"1"`. When restored: flip DRYRUN→`"0"`, restart, self-send to the doctor's own number — **no code change.** | **§7.1** + Archive §S172 |
| **F-83** | **S176 · OPEN (mitigated)** | **Asset-app intake background OCR thread is fire-and-forget** — it dies on service restart and skips non-draft bills, so a read can be lost with no visible trace (why bill B-0001 arrived blank). Mitigated LIVE by **A-D23**: visible `ocr_status`, a non-clobber "Re-read with Sarvam" button, and a server-enforced confirm when approving blank fields. **Durable fix owed** (queue + worker, or synchronous extract with a bounded timeout) — A-D25 candidate. | **§7.1** + Archive §S176 + `KB_Asset_Register` §7 |
| **F-84** | **S179 · FIXED** | **Three self-found security faults in the finance module, all the same shape — an offline-testing convenience carried into production.** (1) reads ungated → fail-closed `before_request` allow-list; (2) identity from spoofable `X-Clinic-*` headers in prod (full control, not a leak) → signed SSO cookie authoritative, header auth opt-in only, *signed-in ≠ entitled*; (3) the SSO epoch never checked → "sign out everywhere" did not revoke here → read live and fail closed, `healthz` surfaces `sso_epoch_ok`, installer auto-rolls-back. **THE LESSON: the offline-testing shortcut WAS the vulnerability.** Extends F-63/F-68. | **§7.1** + Archive §S179 |
| **F-85** | **S180 · CLOSED by correction** | **A session number was assigned by anticipation instead of by close-out.** A document headed "Session 181" was written before the S179 close-out had run; the error propagated forward one more session. Two documents carried wrong numbers and a third nearly did. **RULE: a session number is assigned by a close-out, never by anticipation.** Kin D188, F-54. | **§7.1** + Archive §S180 |
| **F-86** | **S180 · FIXED before install** | **A reader for a PHI source emitted full phone numbers, because it was written against the source's shape rather than the destination's rules.** `marg_report.py` carried the full 10-digit number into its CSV; `patient_ref` stores `phone_last4` and nothing more, and `ingest_column_map` has no phone field at all — exposure with no purpose. Now `phone_last4` only; the item CSV carries no patient identity; outputs grepped for any 10-digit string. **RULE: the destination's constraints are part of the specification.** Kin F-31/F-49, F-46. | **§7.1** + Archive §S180 |
| **F-87** | **S180 · HIGH (process) · remedied by an asset** | **A change was shipped twice to a test suite that could not be run offline** — `finance_app.py`'s smoke is written against the real store, so it would not run here, and the change went on reasoning alone. It broke two assertions on the box; the install gate rolled it back correctly. **This is F-84's own lesson repeated after this project had already minted it.** Two traps now written into the code: `ingest_day` **supersedes and deletes** the day's previous batch, and resolving a queued line **adds** a `sale_item` an earlier check counts. **The remedy is an asset: `dev_seed_smoke_db.py` + differential verification** (baseline vs modified on identical seeded data). **RULE: if a test suite cannot be run, making it runnable is the FIRST task.** | **§7.1** + Archive §S180 |
| **F-88** | **S180 · FIXED** | **A passing `md5sum -c` proved a kit internally consistent, not current.** Two install attempts ran an older download; a stale kit's checksums match its own files perfectly, so the hash gate silently permitted the wrong build twice. Fixed: the installer carries the **identity of the build it belongs to** (`KIT` name + expected md5 of the file that actually changed), checks it first, and refuses otherwise; re-issued kits take new folder/zip names. **RULE: a checksum proves integrity, never currency.** Kin D188, F-66. | **§7.1** + Archive §S180 |
| **F-89** | **S180 · HIGH · cause corrected, loss permanent** | **The cold-backup cadence lapsed for nine sessions, and three canonical documents were lost.** 26,745 files were hashed across the owner's drives (by md5, not filename); four rows recovered, three gone — `KB_Asset_Register` v1.11.0 (Tier-1 CURRENT), `KB_Register` v5.0, `KB_History_Archive` v1.26 — all **S177–S178 outputs, created nine sessions after the last cold kit (S171)**. Every document that *was* recovered came from a backup mechanism that had actually run. **The loss was not caused by the Phase 0 that found it; Phase 0 is the only reason anyone found out.** Restored at the S180 close (`KB_S180_close.zip`). **RULE: the cold kit is not discretionary — it carries a session count, checked at every close.** Consequence recorded under **D316**. | **§7.1** + Archive §S180 |

| **F-90** | **S181 · RULED (D320)** | **The GitHub repository is PUBLIC.** Raised at S181 with visibility UNKNOWN; **proven public at S182 by an anonymous clone**, which converted the suspicion into a fact and answered F-9's long-open question. Recommendation at the time: private + read-only deploy key. **Ruled at S182 (D320):** the repo stays public, knowingly, with the binding corollary that no PHI-bearing artefact may enter it. | **§7.1** + Archive §S181 |
| **F-91** | **S181 · OPEN (behavioural)** | **UPI is recorded as Cash at Docterz entry** — ₹17,900 over six weeks. **Invisible to any ledger-internal check**, because the books are internally consistent either way: only a comparison against the bank exposes it. The typed daily tab is the reconciliation anchor. The fix is the reconciliation workbench (Marg ⋈ bank ⋈ entry, cash→UPI suggestions graded like D315 and never auto-applied), designed at S184. Its shape reappeared in the pharmacy at S182 — two 100%-cash Marg days, ₹38,355 — and was settled at S183 as a Marg UPI-recording gap, bank-confirmed. | **§7.1** + Archive §S181 |
| **F-92** | **S181 · OPEN** | **Discount capture stopped on 18 Jun 2026** — ₹1,33,720 recorded up to that date, then zero. Concessions are still being given; they are simply no longer valued anywhere. Part of an 18–19 Jun regression cluster. | **§7.1** + Archive §S181 |
| **F-93** | **S181 · OPEN** | **The concession parser swallows the Docterz footer**, manufacturing three fake "patients" a day in the staff-facing sheet. Cosmetic in money terms, corrosive in trust terms — a staff-facing report that visibly contains nonsense trains people to ignore it. | **§7.1** + Archive §S181 |
| **F-94** | **S181 · CLOSED by D317's rules** | **An installer's environment assumptions are part of its specification.** The C1a/C1b/C1c red trilogy: three consecutive installer reds, each caught by a gate with nothing half-installed, each traced to an assumption about the target environment that the kit had never stated. Closed by the D317 kit-chain rules rather than by a code fix. | **§7.1** + Archive §S181 |
| **F-95** | **S181 · CLOSED by rules** | **A synthetic store proves logic, not life.** Smoke checks must print what they actually saw; invariants must be asserted as invariants; and an offline store must be enriched with live-shaped data before a first live gate is attempted. Kin of F-87 (a test suite that cannot be run) and F-106 (a test that freezes a data state). | **§7.1** + Archive §S181 |
| **F-96** | **S182 · RULED (D320)** | **The canonical set is PHI-bearing in a public repository** — 7 unmasked patient mobiles, ≥2 patient names and 1 clinic patient ID across 48 files. **A passing 48/48 conceals it:** the check proves integrity and says nothing about whether the content belongs there at all. F-88 one level up. | **§7.1** + Archive §S182 |
| **F-97** | **S182 · STRUCTURAL FIX SHIPPED S183 (D321)** | **Phase 0 verifies documents; nothing verified the Register's live-code pins.** `portal.py` was pinned `da417709…` while the box ran `34f038a765…` — stale by two sessions, with the repo agreeing byte-for-byte with the stale pin. A full-file replacement would have deleted two live finance tiles with every gate passing. Fixed structurally at S183 by `verify_live_pins.py` (D321). | **§7.1** + Archive §S182 |
| **F-98** | **S182 · CLOSED (S182_P2a)** | **The SSO broker treated a trusted device with no SSO session as *the doctor***, reaching every `@doctor_required` surface. F-84's pattern in the front door. Fixed keyed to `_sso_ready()` so D264's inert-on-failure invariant survives. Also the cause of the "missing tiles" report — with no identity, every grant-only tile vanishes. | **§7.1** + Archive §S182 |
| **F-99** | **S182 · OPEN** | **A missing-day alarm anchored on `MIN(business_date)` cannot see a unit that never files a first day** — "not started" and "gone dark" are indistinguishable. Medical was seeded with 121 legacy days and never hit it; clinic is the first unit to start empty, and lab will hit it too. *(Partly relieved at S184 by D322's holiday classifier, which stops Sundays and clinic holidays from being owed at all — but the zero-anchor blind spot itself remains.)* | **§7.1** + Archive §S182 |
| **F-100** | **S183 · CLOSED same session** | **`push_kit.bat` reported "pushed successfully" while git had silently dropped a kit file.** The pin list was named `live_pins.tsv`; `.gitignore` carries a blanket `*.tsv` (a PHI guard — F-31/F-49, D320), and `git add <folder>` says nothing about ignored files inside it. The published kit was incomplete and surfaced only as a SUMS refusal at the VPS console. **The publishing record claimed a file that was not there — F-97's shape one layer up the toolchain.** Fixed by renaming to `.txt` (**no hole punched in `.gitignore`**) + `push_kit.bat` **v4**, which lists any excluded file with the rule that excluded it and REFUSES to commit. **RULE: a publishing step that cannot prove it published everything has not published anything.** | **§7.1** + Archive §S183 |
| **F-101** | **S183 · CLOSED, corrected** | **Eight live files were recorded one directory too high.** The call-hook/verdict family lives in `/root/wa/call-hook/` and `/root/wa/recordings-archive/`; the Register said `/root/wa/`. Confirmed against three independent sources: the files, `call-hook.service`'s `WorkingDirectory`, and four live crontab lines. Seven of the eight matched their pinned md5 exactly — right bytes, wrong address. **The lesson is severity, not bookkeeping: a wrong path downgrades a DRIFT to a MISSING**, and "not there" reads as a filing error while "different from the record" reads as danger. The eighth row proved it — a genuine stale hash (F-102) was wearing a MISSING's clothes. **RULE: a pin is an address AND a hash, and the address is verified with the same seriousness as the hash.** | **§7.1** + Archive §S183 |
| **F-102** | **S183 · CLOSED, corrected** | **`call_hook_capture.py` was pinned at its S126 value while the live file had been replaced on 12 Jul 2026.** 42,409 bytes / 894 lines on the box against 31,490 / 701 in the record; stale across the whole S140→S182 run and carried unchallenged through every Register bump. **A second confirmed instance of F-97's class, and an instructive inversion of it** — at S182 the repo agreed with the stale pin and the box was right; here the repo was right and only the record was wrong. **The record is the weak point in both directions, which is why the check must interrogate the machine.** No harm done: the receiver was measured healthy in the same breath (dual-key gate ON, 26 accepted / 0 refused, service start later than the file's mtime). Found on the checker's first run — the argument for D321. | **§7.1** + Archive §S183 |
| **F-103** | **S183 · OPEN (structural)** | **The finance system reconciles UPI against ICICI but has NO cash-deposit reconciliation against Yes Bank.** Sanjeevni cash is swept ~weekly to a Yes Bank account (`CASH DEP-SELF-SANJEEVNI MEDICOS`); ICICI (…312505) receives card/UPI only. Because nothing matched cash deposits to Yes Bank, **16 real deposits (₹16,45,600, 9 Apr → 13 Aug) went unrecorded** and the drawer chain broke to an impossible −₹30,056 — read for months as missing money when nothing was missing. **FIX owed:** a Yes Bank cash-deposit reconciliation parallel to `finance_upi`, plus a named "bank deposit (Yes Bank)" movement type so a sweep is recorded and never left as a carry-forward break. *(The 16 deposits themselves were booked at S184 by `S184_C1a`; the reconciliation mechanism is still owed.)* | **§7.1** + Archive §S183 |
| **F-104** | **S183 · OPEN (owner chose the fix)** | **The S183 Marg backfill fed identity-less legacy bills through attribution**, creating ~2,062 review items + 118 `line_sum_vs_day_total` exceptions. April→mid-June bills carry a name but no clinic ID, so they route to review (D315 low-confidence), leaving the attributed sum below the day total. **No money affected** — attribution never moves `day_line` (D313). Owner ruling: **reclassify legacy no-ID bills to WALK-IN**. To build + test offline, then apply. | **§7.1** + Archive §S183 |
| **F-105** | **S184 · CLOSED — the system was right** | **The app blocked a data catch-up, and the block was correct.** Darpan's 14/15 Aug entry was refused by the Submit guard because the opening carried the −₹30,056 and the guard will not accept a negative opening. **The S183 record had explicitly said this catch-up "needs nothing above" — the record was wrong and the box was right.** The D313 invariant doing its job. **RULE: the app enforcing correctness looks like an obstacle and is a feature; when the record and a running guard disagree, believe the guard.** | **§7.1** + Archive §S184 |
| **F-106** | **S184 · FIXED (S184_F1b)** | **A self-test that asserts a DATA STATE becomes a liability the instant the data is legitimately corrected.** `finance_app.py --selftest` asserted the *pre-S184* store state — cash negative, breaks open, marg unmapped — so the session's own correct migrations read as test failures and the install gate correctly restored. Made **state-adaptive** in F1b: 314/314 on the corrected store. **Same family as F-88 (integrity ≠ currency) and F-97 (a pin agrees with a record, not reality).** **RULE: separate invariant logic from store state; the latter must be state-adaptive or fixture-based, never frozen.** Follow-up owed: split the selftest into invariant-logic vs seeded-fixture checks. | **§7.1** + Archive §S184 |
| **F-107** | **S185 · OPEN (structural) · both docs filed + pinned** | **Phase 0 is blind to a document that was never listed.** The S184 close wrote two **Tier-0** documents (`HANDOFF_RUNBOOK v118`, `START_HERE_SESSION_185`) into project knowledge only — never to the repo, never into `MD5SUMS_ALL.txt`, never as manifest rows. **So at the S185 open, the two Tier-0 documents Phase 0 is *required to read* were the two it *could not verify*.** They were read on trust and nothing complained, **because nothing looks for a missing row**: Phase 0 asks of each listed row *do these bytes still match?*, never of each document in use *are you listed?* **F-97's documentary twin — both are absence-blindness.** Remediated at S185 (both filed, hashed as delivered, pinned; hashes deliberately **not** invented). **Structural fix still owed: the inverse Phase-0 check.** | **§7.1** + Archive §S185 |
| **F-108** | **S185 · OPEN · index corrected here** | **Findings recorded in the KB Register's index were never applied to this register, and its §7 index has been stale at F-89 for four sessions.** §7 ended at F-89 and read *"Next free finding: F-90"* while **F-90 … F-95 (S181) had never landed here at all** and F-96 … F-99 (S182) existed only as §7.1 text with no index rows. The KB Register carried all of them, so nothing was lost — but **the findings register was four sessions behind and said so nowhere.** **This is the F-45 family recurring** — the fault this register minted at S149 for exactly this failure, reconstructed six times at v2.17, and committed again at v2.18 (which bumped the file and left no changelog row). **RULE: the next-free number and the last index row must agree, and that agreement is checked at every append.** | **§7.1** + Archive §S185 |

| **F-109** | **S186 · CLOSED — record corrected** | **Two characters of a hash were invented to make a partial pin look longer than the evidence.** The S184 close recorded `finance_app.py` as eight characters, `c66bec2b`; the S185 fold-in wrote it as ten, `c66bec2b76…`, in fourteen places — while stating in the same breath that the value "was NOT invented". The box and the `S184_F1b` kit both say `c66bec2b9e…`. Nothing downstream broke **because a partial pin is never machine-compared**, which is exactly why it survived a session. **RULE: a partial hash is quoted at the length the evidence supports, never rounded up; and "I did not invent this" is a claim to be checked, not trusted.** | §7.1 · Archive §S186 |
| **F-110** | **S186 · FIXED (kit `S186_V1a`)** | **The live-pin checker was holding the box to a Register draft that never became canonical.** `/root/deploy/live_pins.txt` declared `source_md5: ff509b01…` for `KB_Register_v5_5_S183.md`; canonical v5.5 is `3cad79e6…` and **no file in the repo hashes to `ff509b01…`**. Two of three DRIFT reds at the S186 open were therefore **false** — the record was right and the checker was behind it. The tool printed its own source md5 every run for three sessions and **nothing compared it to the manifest**. A third instance of F-107's absence-blindness, inside the tool built to close F-97. **RULE: a checker that can be stale must verify its own source before it verifies anything else, and refuse to run rather than report.** | §7.1 · Archive §S186 |
| **F-111** | **S186 · FIXED (kit `S186_V1a`)** | **The Register and its own generator drifted apart, and nothing noticed because nobody re-ran the generator.** `live_pins.txt` had not been rebuilt since S183, so three later changes to the Register's live-file table were never tested against the tool that consumes it: two `*(applied marker; no file md5)*` rows **halt** the generator outright, and a `*(superseded)*` rollback row would have been pinned as a **second live pin for the same path** — a red that could never go green (D316). **RULE: a generated artefact that is not regenerated every session is not a check, it is a souvenir.** | §7.1 · Archive §S186 |
| **F-112** | **S186 · FIXED (kit `S186_C1a`)** | **A bank deposit that never happened was booked into the live financial books.** `S184_C1a` booked "16 verified Yes Bank credits, ₹16,45,600". The statement for 1 Jul – 17 Aug has its **last transaction of any kind on 30 July**; the 13 Aug ₹75,000 does not exist. Truth: **15 deposits, ₹15,70,600**, and the books understated cash by ₹75,000. **S183 had flagged that exact row** — *"owner-confirmed; it falls after the statement cutoff … check when booking"* — and it was booked without the check. **RULE: a row the record itself marks as unevidenced may not be booked until it is evidenced — a caveat carried alongside a number does not travel with it into a migration.** | §7.1 · Archive §S186 |
| **F-113** | **S186 · FIXED (kit `S186_I1a`, portal path)** | **"not filed (refused, harmlessly)" is only harmless until the day is filed.** `marg_backfill.py` skips a day with no `day_entry` and reports it on the console. At the 16 Aug run, 14 and 15 Aug were not yet filed, so both were correctly skipped — and **nothing revisited them**: no flag, no exception, no marker, only a console line from a run that had already finished. Distinct from F-100/F-112, which are silence about what was never reached: **here the tool spoke, correctly, and the statement expired.** **RULE: a skip that depends on the state of the world must leave a record that outlives the run.** *(Diagnosed twice wrongly first — a short export, then a driver abort — and settled only by testing the real file and the real adapter. D172/D188 applied to a diagnosis rather than a hash.)* | §7.1 · Archive §S186 |
| **F-114** | **S186 · FIXED (kit `S186_I1a`)** | **Two records described WALK-IN attribution that the running code did not perform.** `marg_report.py` warned *"…will attribute to WALK-IN"* and `finance_ingest.resolve_patient`'s docstring said *"a line with no ID lands on WALK-IN"* — but a gate three lines above diverted the line first, so a bill with **neither ID nor name** was parked in a review queue **containing nothing a human could resolve**. 2,062 rows by S186, ~10 more every clinic day; on 14–15 Aug: WALK-IN 0, review 10. **RULE: a review queue is for lines a human can resolve; anything else is a queue that can only grow.** | §7.1 · Archive §S186 |
| **F-115** | **S186 post-close · FIXED (`PUBLISH_CLOSE.bat`)** | **The default publish method is structurally unable to publish a close-out.** `PUSH.bat` stages exactly one path — its own kit folder. `KB_canon_all` is not a kit and has no `PUSH.bat`, so no per-kit publish can ever carry the canonical set. The S186 close was pasted, pushed, and reported clean while the entire canon sat uncommitted in the working tree. |
| **F-116** | **S186 post-close · FIXED (manifest rebuilt)** | **The manifest pinned the current Register at a hash no file in the repo carries.** Its Register *row* was right (`d0da61a0…`); its own Phase-0 footer said `d5ec45a5…`, a token appearing in exactly one place in the whole repo — that footer. A phantom inside the linchpin. |
| **F-117** | **S186 post-close · list FIXED (`S186_V1c`); TOOL FIX OWED** | **The pin list attested to a manifest that does not exist, and the checker printed the claim without testing it.** `live_pins.txt` carried `manifest_md5: 04eff42c…`; the published manifest is `d1f97e1a…`. `verify_live_pins.py` v1.1 reads the word `yes` and prints "VERIFIED against the manifest (md5 …)" — it never compares that md5 to a real file. F-110 one level up, inside the tool built to close F-110. |
| **F-118** | **S186 post-close · FIXED (Register v5.12)** | **A duplicate-pin conflict was resolved toward the superseded build, and the first live-pin run went RED because of it.** `finance_workbench.html` shipped twice (`S186_R2a` `45cb85b3…`, then `S186_I1a` `18c71e63…`). The box has carried the I1a build since that kit installed. The close kept the R2a value. **The first RED in this project caused by the record rather than the box.** |
| **F-119** | **S186 post-close · FIXED (`MD5SUMS_ALL.txt` rebuilt)** | **Phase 0's only command failed, because the checksum file listed a file that does not exist.** `MD5SUMS_ALL.txt` carried a row for `KB_Register_v5_10_S186.md`, an intermediate bump not in the canon set: 70 rows OK, one "No such file", non-zero exit. The door to the next session was locked and nothing said so. |
| **F-120** | **S186 post-close · FIXED (attic)** | **Three competing checksum files described the same folder and two were stale.** `MD5SUMS_ALL.txt` (71 rows, authoritative), `SUMS.md5` (52 rows, 4 mismatches), `MD5SUMS.txt` (10 rows, 1 mismatch + a malformed line). Nothing read the latter two. D202's one-authored-source rule, broken inside the folder that rule exists to protect. |
| **F-121** | **S186 post-close · FIXED at v3, after v2 failed the same way** | **A gate widened in scope began firing on deliberate ignores.** v1 of the new publisher inherited F-100's "any excluded file is suspicious" check but widened `git add` from one kit to the whole tree; it then refused the commit over `.pyc` residue in two S182 kits and a stray `.tsv` — all correctly ignored, none in the payload. It refused for the wrong reason, and nothing was committed: a safe failure, but the kind that teaches an operator to wave gates through (D316). |
| **F-122** | **S187 · CLOSED STRUCTURALLY (kit `S187_V1a`)** | **The pin-list generator minted a phantom manifest hash at every generation, and the checker published it as a pass.** The manifest's self-row is *"recomputed last, each EOS"*, so its whole-file md5 at generation time is transient **by construction** — `S186_V1c`'s `manifest_md5: 78881ddd…` and V1b's `04eff42c…` match no file in any of the repo's 157 commits. Fixed in v1.2 of both tools: the generator writes the stable `manifest_current_register_pin`; the checker **proves the claim on the box** (hash-hunt in `/root/deploy/repo` canon + manifest CURRENT-row parse) and cannot print VERIFIED without proof. **RULE: never attest to the hash of a file whose rules say it will change after you hash it — attest to the stable value inside it that constitutes the claim.** | §7.1 · Archive §S187 |
| **F-123** | **S187 · FIXED at this close (attic'd + renamed)** | **The repo carried two divergent `CANONICAL_MANIFEST.md` copies, and the stale one still called itself canonical.** `canonical-docs/CANONICAL_MANIFEST.md` was nine sessions stale (S177) with "STATUS: canonical" in its own header, beside sixteen superseded doc versions, covered by no checksum file. F-120 one level up: rival checksum files became rival manifests. Retired: the folder moved to the attic, its manifest **renamed so it cannot pass for a live one**; a pointer README left behind. **RULE: exactly ONE file in the repo may be named `CANONICAL_MANIFEST.md`, and a superseded self-describing document must be made to say so.** | §7.1 · Archive §S187 |
| **F-124** | **S187 · FIXED same session (`PUSH.bat` v2 → `PUBLISH_ALL.bat`)** | **The publisher swallowed a fatal and printed success.** A stale `.git/HEAD.lock` blocked the commit; `\|\| echo (nothing new to commit)` read the fatal as an empty commit; "pushed" was printed with origin unchanged. The fourth publishing fault in three sessions (F-100 · F-115 · F-121), all the same shape: **the tool asserted an outcome it never verified.** v2 refuses on a lock, distinguishes empty from failed BEFORE committing, and prints success only after origin HEAD = local HEAD. **RULE: `\|\| echo` is how a fatal becomes a footnote; a publisher may print "pushed" only after comparing the remote to the local head.** | §7.1 · Archive §S187 |
| **F-125** | **S187 · FIXED (kit `S187_P1b`)** | **A selftest asserted store state and was broken by the first real datum.** The M1a-era check *"staging holds exactly one pending row"* counted ALL pending pushes; the morning's **first genuine push from the medical PC** made it two, and the P1a install went RED **388/389** — the gate restored byte-perfect, no incident. The **fourth firing of the F-106 family** (F-84's fourth lesson, F-87, F-106). Fixed by scoping the check to its own bytes (`file_md5 = md5(stub)`), then **re-rehearsed against the exact failing condition**. **RULE: a test asserts behaviour, never store population — and a fixed test is re-run against the state that broke it.** | §7.1 · Archive §S187 |
| **F-126** | **S187 · FIXED (rule standing)** | **An installer's goodbye message aborted the run after all real work had succeeded.** A sed-injected echo in `install_h1a.sh` broke shell quoting in the script's tail; the page was already placed and pinned, so the "failure" was cosmetic — but an installer that dies after acting is indistinguishable from one that died before. Cause: string-surgery on a shipped installer, syntax-checked only along the rehearsed path. **RULE: every installer is syntax-checked WHOLE (`bash -n`) before shipping — a rehearsal exercises one path; `bash -n` reads them all.** Applied to H1b/H1c the same session. | §7.1 · Archive §S187 |

| **F-127** | **S188 · FIXED + INSTALLED (kit `S188_D2a`)** | **A role gate on the surface is not a role gate on the data.** `/finance/api/tile` carried no `require(...)` at all. `_gate` demands *a* role on the medical unit, so it was never open to the world — but it does not distinguish maker from checker, and **Darpan's entry page fetched it on every single load** to render one deposit banner. What his browser actually received: `cash_in_hand`, `cash_with` (the custodian's NAME), `month_to_date`, `last_revenue`, `deposit_threshold`, `deposit_excess`, `last_bank_deposit`, `days_since_bank_deposit`, `noncash_month_to_date`, `awaiting_approval`, `last_month_close`, and every shout count. `/finance/api/exceptions` was the same shape. **The F-84 family one layer in:** F-84 closed three ungated reads at S179 and these two were not among them, because the unit gate made them *look* protected. Fixed: `tile` → checker-only; `exceptions` → a maker receives only `missing_day`; `day/<date>` gated (payload already correct). **RULE: a route states its own role. A gate that protects the unit boundary does not protect the role boundary inside it, and a route that needs `checker` and forgets to say so silently accepts the maker.** | §7.1 · Archive §S188 |
| **F-128** | **S188 · FIXED (harness corrected in `dev/dev_seed_smoke_db.py`)** | **The offline rehearsal harness made eight role-refusal assertions pass by accident.** `dev_seed_smoke_db.py` seeded `unit_role(medical, selftest, checker)`. The live box has **no such row**, so on the box the header role alone decides — but in every offline rehearsal the smoke user silently carried checker rights, and every *"a maker cannot cutover / post statements / allocate deposits"* assertion was testing nothing. Found only because F-127's fix **is** a role refusal and would not go green. Correcting one line moved the offline baseline **375 → 398**. **This is the F-106 family living inside the harness that tests for the F-106 family** — the fixture granted the very privilege the assertions existed to deny. **RULE: a test fixture must not grant the privilege the test exists to refuse; a refusal is asserted from a seat that genuinely lacks the role.** | §7.1 · Archive §S188 |
| **F-129** | **S188 · FIXED + INSTALLED (kit `S188_D2b`)** | **A marker recorded that something was shown, but not who it was shown to — so it spoke about the wrong person.** D2a's `day_mirror_reveal` was keyed on the DAY, whoever opened it. The checker glancing at a draft armed the badge; the **maker** was then stamped `EDITED_AFTER_REVEAL` for a check he had never been shown. The flag would have been *literally true* — the figures did move after the day was cross-checked — and would still have accused the wrong person, quietly eroding the one thing stage D2 exists to protect. **Near relative of F-118:** the row asserted something about the maker's sequence that it had never observed. Fixed: the reveal arms only when the caller holds `maker` and not `checker`; the endpoint reports `looking_as_maker` / `armed_by_this_look`; the page renders a read-only row for a checker's look. **RULE: a marker that records "this was shown" must record WHO it was shown to, or it will speak about somebody else.** | §7.1 · Archive §S188 |

| **F-130** | **S188 close · OPEN · fix specified, 3 lines per page** | **A page-only kit that preserves every id is invisible to an id-based test — so the design is the one thing the gates cannot see.** The H1b/H1c Hub redesigns shipped deliberately with every element id and API path byte-preserved, which is what made them safe. It is also what makes them **undetectable**: a page could silently revert to an older design and all 464 checks would stay green. Exposed when a saved copy of `/finance/approvals` turned out to be the pre-H1c design and **no gate we own could tell it from the live one** — only a direct `md5sum` on the box settled it. **Remedy, already half-applied without noticing:** the S188 entry-page suite asserts a *design fingerprint* rather than an id — `--surface-page:#f3f2ee`, `id="toTop"`, `class="kick"`, the folded-help block. The same three lines on `approvals`, `workbench` and `review` close it. **RULE: when a kit deliberately preserves every id, the test must assert something the kit did NOT preserve — otherwise the change and its absence are indistinguishable.** | §7.1 · Archive §S188 |
| **F-131** | **S188 close · FIXED in practice (`--no-optional-locks`) · 14 files owed a delete** | **`git status` is not a read-only command, and four sessions of evidence sat unread in `.git/`.** `git status` refreshes the index, which means creating and then deleting `.git/index.lock`. On the desktop-bridge mount **deletes are forbidden**, so the lock survives and blocks every subsequent write — including `PUBLISH_ALL.bat`. Git says so at the time (*"unable to unlink … Operation not permitted"*), and that warning was read past. **`.git/` holds FOURTEEN of these**, dated across **S185, S186, S187 and S188** — `stale_1786905261`, `stale_S185_safe_to_delete`, `stale_S186`, `s6`, `s7`, `sD`, `z3`, `z4`, `cleared_final`, `stale_S187close`, `stale2_S187close`, `stale4`, and two from this session. **Every session hit it, renamed the lock, and moved on; not one recorded it**, so each rediscovered it from scratch and this one lost a publish to it. **The F-45 family in its purest form** — a known problem with no entry — compounded by **F-119's** lesson applied to a human instead of a script: *a warning is a failure*. **Fixed in practice:** `git --no-optional-locks status` reads the same state and provably leaves nothing behind; no bare `git` command is run against the mount again. **Owed:** the owner deletes the 14 files (the bridge cannot). **RULE: a command that looks read-only is not read-only until its side effects have been checked — and a workaround repeated without a record is a fault that will be rediscovered, not a fault that was solved.** | §7.1 · Archive §S188 |

| **F-132** | **S188 post-close · FIXED + INSTALLED (kit `S188_D2c`)** | **A claim recorded as fact, and never tested — the maker's page was showing the running unit balance.** `opening_p` comes from `v_cash_ledger`, whose window is `ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING`: a running total of **every day since the books began**. The maker's page labelled it *"Opening cash · carried from the last filed day"* and rendered it at 24px, with "Closing cash" below at 30px. **D2a gated that route hours earlier and recorded — in the kit, the Register and to the owner — that its payload was "already correctly scoped".** Nobody looked. *A checker may not print a claim it did not test*, applied to the person writing the record. **Worse than the disclosure: it was not TRUE of him** — most of that balance is parked with Dr Bhawna (D323) and ₹87,205 is a pre-April adjustment (S186), so "carried forward" invited him to believe the drawer held two lakh. That half predates F-127 and had been live since **S179**. Leaked through **three** doors: the GET, the **save response**, and the D2 mirror. Fixed: withheld from a maker on all three; the checker unchanged; the page's opening/closing display removed. **Nothing weakened — the carry-forward is safe because it is COMPUTED and never accepted from a client, not because it is displayed.** **RULE: "already correctly scoped" is a test result or it is nothing. A payload named for one day may still carry a window over all of them.** | §7.1 · Archive §S188-POST |
| **F-133** | **S188 post-close · OPEN · code is not what is broken** | **The feature exists, has existed since S179, and has never once been used.** Asked to show cash parked with Dr Manoj and Dr Bhawna, the box was surveyed before building — and the survey was the finding: `cash_movement` for medical contains **only** `bank/out`, 15 rows, ₹15,70,600 (the S186-verified deposits); **no row for either doctor, ever**; `cash_custody_event` **empty**. Building the display unsurveyed would have shown a confident **`Dr Manoj ₹0 · Dr Bhawna ₹0`** in the clinic's own software while roughly **two lakh** sat with one of them — a worse falsehood than the one being removed. **It also explains the ₹2,05,198**: S184/S186 recorded *"cash parked with Dr Bhawna"* as **exception text**, never as **cash movements**, so the ledger has counted parked money as in-hand ever since. The money left the room; in the books it never did. Mitigated in `S188_D2c` by rendering the zero as an **instruction, not a fact**. **Still owed: the ledger's "cash in hand" is overstated by whatever is genuinely with the doctors, and no record exists to net it down** — closing it needs the handovers entered retrospectively, or a counted reconciliation like S186 did for the drawer. **RULE: survey the box before building a display of its data — a zero rendered from an unwritten table is indistinguishable from a zero that is true.** | §7.1 · Archive §S188-POST |

| **F-134** | **S188 final · FIXED (routine gains step A8; list regenerated)** | **A close-out step performed once and never written down was skipped the next time.** `live_pins.txt` is generated **from the KB Register**, so a Register bump makes it stale by definition. S187 regenerated it at its close and recorded that it had — in the manifest's §S187 block. But **`END_OF_SESSION_PROMPT_v4` §A has no step for it**: §A7 makes the manifest "always updated last" and stops there. So the S188 close rebuilt the manifest, `MD5SUMS_ALL.txt` and `KIT_ID.txt`, and left the pin list on **Register v5.22 — three versions stale**. The owner's own close-out run then went **RED on `finance_app.py` and `finance_entry.html`: two files the box had exactly right.** **The tool was flawless** — it refused to print VERIFIED, reported `MANIFEST_MISMATCH`, and showed the CURRENT pin it expected beside the one the list carried (F-122's v1.2 fix, working as designed). **The F-45 family**: a step done by hand, recorded as narrative rather than as procedure, and therefore not repeatable. **Fixed:** the routine gains **step A8 — regenerate the live-pin list, AFTER A7**, because it depends on the Register *and* on the manifest that pins it; and the list is regenerated here from v5.26 with `register_pin_verified: yes`. **RULE: a derived artefact must be rebuilt in the same routine that changes its source — and "someone did it last time" is narrative, not procedure.** | §7.1 · Archive §S188-POST |

| **F-135** | **S189 · FIXED in the build (kit `S189_G1a`)** | **A remediation instruction named three pages; two of them do not carry the thing it asked to assert.** Runbook v124 §2 ⭐1 and START_HERE 189 §A both said: add the design-fingerprint assertions to the served-HTML checks for `approvals`, `workbench` and `review`. Surveyed on the real bytes before a line was written — **approvals 4/4 markers; workbench 0/4; review 0/4** — because the workbench is the `S187_M1a` build and the review page is the untouched S179 build, **both older than Clinic Design Language v1 itself**. Two thirds of that instruction would have gone RED at its own gate. It was written at the S188 close from the *shape* of F-130 rather than from the files: **"add this assertion to those three pages" is a claim about those three pages, and it was not tested** — F-132 recurring in the record instead of the code. Fixed by declaring the measured state in **both** directions, the two pre-v1 pages asserted NEGATIVELY, so a later rebuild cannot land silently either. **RULE: a remediation instruction is a claim about the thing it names, and carries the same burden of proof as any other claim.** | §7.1 · kit `S189_G1a` |
| **F-136** | **S189 · OPEN · fix specified (strip the md5, keep the pointer)** | **The manifest keeps its own copy of a value it says the Register owns, and nothing checks the copy.** The Tier-2 Attendance row reads *Staff Ledger app `staff_ledger.py` v2.4 `74dac84e…` (separate live system, **Register-tracked**)* — it names the Register as authority and carries the value anyway. Register v5.26 pins `/root/staff_ledger.py` at `92665b64…` (S162/S164) and does **not** contain `74dac84e…` anywhere. **Measured on the box at S189: the file is `92665b64…` — the Register is right and the manifest's copy matches nothing there.** The gap is structural: `gen_live_pins.py` builds the pin list **from the Register**, so a hash living only in the manifest never enters the list and `verify_live_pins.py` has never seen it; Phase 0's F-88 cross-check asks only whether a token is a *document* and correctly answers no. **A hash present in the manifest but absent from the Register is checked by neither** — unverified since S162. Also found: an untracked `/root/wa/staff_ledger.py` = `06bf03cb…`, a value that appears **nowhere in the repo**; `staff-ledger.service` runs `/root/staff_ledger.py`, so the stray is wired to nothing and backlog ⭐4's ₹70,000 reads off the file the record knows. **RULE: duplicate a value and you have created a second thing to keep true.** Kin: F-116 (a phantom hash in the linchpin's own footer), F-45/F-108. | §7.1 · manifest Tier-2 |

| **F-137** | **S189 · FIXED + INSTALLED (kits `S189_W1a` · `S189_W1b` · `S189_C1a`)** | **The record diagnosed an overstatement that never existed, and its prescribed fix would have created the very error it described.** Runbook v124 ⭐0b: *"cash in hand is overstated by unbooked handovers … no record exists to net it down."* Reading the schema before building: `v_day_cash` computes `cash_out_p = SUM(cash_movement WHERE direction='out')` — every movement row subtracts from cash in hand, whatever the party — so booking the handovers as `cash_movement` (the endpoint S188 built reads only that table) would have cut cash in hand ₹2,05,198 → ≈₹30,000. The S186 count had already proven the position: drawer 0 · owner ₹18,963 · Dr Bhawna ₹1,56,235 = ₹1,75,198 = the books once Darpan's ₹30,000 is entered. **The custody facts had been recorded — as prose in `cash_count.explanation`, in the same session that built `cash_custody_event` to hold them.** No query reads prose; the card honestly said zero; the backlog chased a phantom. Owner ruling (S189): doctor-held cash IS cash in hand, located elsewhere — custody is LOCATION, movement is QUANTITY. Fixed: the card reads `cash_custody_event` (`S189_W1a`/`W1b`, six checks proving a custody event moves the card and not the ledger AND a movement moves the ledger and not the card) and `S189_C1a` recorded the counted position — 4 rows, the ₹1,45,000 balancing entry admitting in its own note that its journeys are unitemised; ledger proven byte-identical. **RULE: a diagnosis in the record is a claim about the schema, and the schema is read before the fix is prescribed.** Kin: F-132, F-135. | §7.1 · S186 §5 |
| **F-138** | **S189 · FIXED + INSTALLED (kit `S189_W1b`)** | **A discipline applied to the line under the cursor and not to the pattern: three state-asserting checks refused the migration they were written to protect.** C1a ran perfectly — precheck green, verify green, cash untouched — then the final smoke went red on three F-137 checks asserting absolutes ("parked with Dr Manoj must be ₹0.00" · "exactly ₹12,345.00"), true only of a store with no custody rows. The moment the migration legitimately recorded ₹18,963, they were false, and the installer's honest red restored the books — **the gate was flawless; the checks were the fault.** The aggravation that earns the number: a fourth check in the same block had ALREADY been converted to a delta, citing F-106 in its own comment, while its three neighbours were left absolute. F-106/F-125/F-128 family. Fixed: all assertions measure the delta their own inserts produce (`_paise` helper), rehearsed green on BOTH store states. **The count-equal problem met honestly:** 488 → 488, so the W1b installer REPRODUCES the failure — C1a applied to a throwaway copy of the live store; current app required RED with every FAIL naming F-137; new app required GREEN on that copy and on live — before any swap. On the box: 485/488 reproduced exactly, then 488/488 twice. **RULE: when a rule is applied to one line, it is applied to the block — and a fix whose effect a count cannot see is proven by reproducing the failure it cures.** | §7.1 · kit `S189_W1b` |

| **F-139** | **S189 · FIXED + INSTALLED (kits `S189_E1a`/`S189_E1b`)** | **A structured control attributing money to invented identities — worse than free text, because it looks queryable.** The entry page's salary-advance staff selector was hardcoded: `<option value="1">Darpan</option><option value="2">Someone else</option>` — ids into `staff_ref`, a table **empty since S179** that no code in the app ever read or wrote; *"Someone else"* was a fake staff member with id 2. **Surveyed on the box before building (the F-133 habit), and the survey is why this is a finding and not an incident: zero expense rows ever carried a staff_id.** The gun was loaded at S179 and never fired. Fixed: on the medical page a salary advance is Darpan's own (owner ruling — *"Darpan draws only his salary advance from the medical cash"*), the staff selector is GONE, and the **server resolves the identity** at write time (F-84: the client does not get to name who money attributes to), lazily creating the one real `staff_ref` row; a client-sent id is ignored even from an old cached page. Rides with the owner-ruled expense MENU: five categories, one authored source in the app, the served page held to every label by the selftest, a skipped choice refused server-side, Other requiring written details, the advance writing the exact S184 string so history stays one queryable value. **RULE: a dropdown is a claim that its values exist; a control's ids are attribution, and attribution is the server's to decide.** | §7.1 · kit `S189_E1b` |
| **F-140** | **S189 · FIXED + INSTALLED same day (kit `S189_E1b`)** | **The rehearsal store had the live store's schema and not its SHAPE — and the kit was refused by its own gate on the only store with holes.** E1a's selftest hunted a free rehearsal day FORWARD from 1 April. Offline (continuous seed store) that lands on 14 Aug; on the box it lands on the first D322 Sunday hole in early April — **135 days back, beyond `BACKFILL_WINDOW_DAYS=120`** — where the save answers `too_old` BEFORE the expense parse, so all six new checks failed identically and the D317 gate swapped nothing. Diagnosed by **reproduction, not guessing**: a copy given a beyond-window gap produced exactly the box's six FAILs; a mid-window gap produced only three (the refusals parse before the closing guard) — the difference discriminated `too_old` from `negative_cash`. Fixed: the finder searches **backward from today**, the direction the D2/F-129 blocks already use — *a rehearsal must stand where the maker is allowed to stand* — and every check embeds the server's actual error in its label, because the six reds said nothing about WHY and the diagnosis cost a reproduction that a single `(got %s)` would have made free. Rehearsed green on FOUR store shapes before reshipping. Kin: F-87 (the unrunnable offline suite), F-128 (the fixture granting what the test refuses), F-138 (the block, not the line). **RULE: a rehearsal store must carry the live store's shape — its holes, not just its tables — and a check that can fail must say why.** | §7.1 · kit `S189_E1b` |

| **F-141** | **S190 · CLOSED (kit `S190_E2` v2; the gate refused v1, box untouched)** | **A gate constant composed from a narrative prefix, and — the same day, the same root — a delivery note written from memory. Two instances, one fault.** The `S190_E2` installer's clinic-page currency constant was a full 32-character md5 whose HEAD came from the record's truncated `0c64fda2…` and whose TAIL was invented to fill the width: **a value no file has ever had.** The D317 chain stopped at [2/7] against the true live bytes and nothing was touched; an on-box `tr -d '\r'` comparison then proved the payloads themselves were built on the correct live file. Kit v2 changed exactly one constant, transcribed from the owner's own `md5sum` run. **The full correct value had been in the live-pin list the whole time** — the narrative prefix was read where the Register's live-file table is the source. *Second instance, same session, same root:* the kit's delivery note gave the install path as `/root/deploy` for `/root/deploy/repo`, written from memory rather than from the record, and was caught only by the owner running it. Family: F-109 (the invented hash), F-116 (the phantom in the linchpin's own footer), F-135 (the instruction written without opening the file). **The new venue is what earns the number: this family had only ever appeared in documents, and it has now reached an installer's gate — the one place a wrong constant is load-bearing.** **RULE: a hash is transcribed from a measured value or it is not written; a narrative prefix is a pointer, never a pin — and a path in a delivery note is read off the record, not recalled.** | §7.1 · kit `S190_E2` |
| **F-142** | **S190 · FIXED (kit `S190_F3` v2; the gate refused v1)** | **The installer's summary-reader took the last line of the selftest output as the verdict, and the last line was a FAIL.** `S190_F3` v1 was refused by its own gate — correctly, but for the wrong reason: the harness ran the suite and read `tail -1`, which on that run was a failing check rather than the summary line, so the installer could not tell "the suite failed" from "I read the wrong line". The payloads never moved. v2 changed the harness only: it greps the WHOLE output for the summary, and requires the expected fail-set **by name** rather than by position. **This is worse than an ordinary bug and that is why it earns a number: a verification harness that can misreport its own verdict corrupts every result it will ever produce — including the passes.** Kin: F-122 (the checker that printed a claim it had not tested), F-124 (the publisher that printed success over a swallowed fatal). **RULE: a harness that reads "the summary" must first prove the line it read IS the summary — grep the whole output, name the expected failures, never `tail -1`.** | §7.1 · kit `S190_F3` |
| **F-143** | **S190 · FIXED + INSTALLED same hour (kit `S190_SL3`)** | **A quota counter that counted years of history as if it were this month — found by the owner's first live look, and findable no other way.** D331's month-counter summed every `ADVANCE_ISSUE` row by calendar month. The **S155 migration rows carry years of loan history but are DATED August 2026**, so Darpan's inline line read *"Rs 3,63,000 of Rs 15,000"* and his ordinary, entirely legitimate ₹15,000 advance **would have been refused by the gate built to protect him.** No offline store could have caught it: the rehearsal store has no migration rows at all, so the shape that produced the fault does not exist outside the box. Owner rulings, executed the same hour: the quota counts **from the D331 install forward** — pre-install rows are grandfathered (visible in the position card and statement, recovering as normal, never eating a month's quota) — and **interest-bearing loans never consume the ordinary quota**, bypassing its gate as the parallel D250 instrument. Selftest 212 → 214, +2 exactly. Family: F-140 (the store with the schema and not the shape), one layer further out — here even the *shape* was unreachable offline, because the data was historical. **RULE: a counter over dated rows must ask what the date MEANS, not just what it says — and a policy gate meets its real data on the box before it is trusted anywhere.** | §7.1 · kit `S190_SL3` |
| **F-144** | **S190 · FIXED + INSTALLED same hour (kit `S190_F4`)** | **The locked-day gate read the broker's role instead of the unit's, and refused the doctor his own approved day.** The medical save's approved-day guard tested `u["role"] != "checker"` — the **SSO broker** role, legacy header semantics — rather than the unit roles `require()` had already computed. Via SSO the owner's broker role is `doctor`, so the screen told **the doctor** *"This day is already approved — only the doctor can change it."* The clinic twin has carried the correct unit-roles form since S182; **the medical twin never did, and nobody had ever re-edited an approved medical day until that hour** — a defect live for sessions, held shut by the fact that no one had opened that door. One functional line changed; two checks reproduce the owner's exact SSO shape. An audit of every `u["role"]` use in the file found this the **only** wrong one. Family: F-84 (identity taken from the layer that is easiest to reach rather than the layer that is authoritative), F-127 (a role gate on the surface is not a role gate on the data). **RULE: when a broker sits in front of a unit, identity comes from the unit layer — and every `u["role"]` in the file is audited the moment one of them is found wrong.** | §7.1 · kit `S190_F4` |
| **F-145** | **S190 · FIXED + INSTALLED same hour (kit `S190_F5`)** | **A queue that hides a class of rows did not un-hide a row the moment it stopped being that class — so money counted while its day was invisible.** The approvals queue deliberately hides `source='legacy_sheet'` days, so the bulk pre-15-Aug import cannot flood it. The owner edited his 31-July day; the edit made it an app entry in every sense that matters — its ₹10,000 counted in the drawer immediately — but the `source` marker still said `legacy_sheet`, so **the day vanished from the queue while its money was already live.** A correction now re-marks the day `source='app'` on both units, and the `day_revision` keeps the legacy original verbatim. Live smoke 549 → 550, +1 exactly. The exposure is the shape worth naming: **a filter written to protect a queue from a bulk import became, silently, a filter that hid real work needing approval** — the hiding rule outlived the condition it was written for. **RULE: a queue that hides a class must un-hide a row the instant it leaves that class; a classification used as a filter is maintained by every path that can change the class.** | §7.1 · kit `S190_F5` |
| **F-146** | **S190 · OPEN (rule adopted; no code fix specified yet)** | **A refusal that looks like a save — the gate did its job, the red went unseen, and "done" entered the session's belief state anyway.** Before SL3, the owner entered two of the sitting's advances; the migration-dated quota gate (F-143) refused both; the refusal did not read as a refusal on the screen he was looking at; and **both the owner and the assistant carried "the advances are in" forward as fact until `/ledger/book` was queried and proved absence.** Nothing was corrupted — the gate was right and the money never moved — but the session operated on a false belief for a stretch, and only a query against the book dislodged it. **This is the one candidate that cost something real, and it is not a bug in any single place**: the gate behaved correctly, the page rendered, no exception escaped. The fault is that a refusal and a success were not distinguishable at a glance, and that neither party verified against the store. Kin in spirit: F-132 (a claim about a screen that nobody had opened), F-124 (success printed over a fatal). **Owner-facing consequence:** it is the reason every entry in this session's sitting was afterwards confirmed in the book rather than on the form. **RULE: verify entries in the BOOK, never on the form — and a refusal must be impossible to mistake for a save. The UI fix is specified as owed, not built.** | §7.1 · Runbook v126 §1.3 |
| **F-147** | **S191 · CLOSED S192 (kit `S192_SL6` — the capacity rule is live)** | **The close records recovery the salary could not pay.** D250 rules: *"if salary can't bear all, the instalment skips and the tracker prices it."* The clause was never built: `close_month()` writes the quota lane's full balance and the waterfall budget unconditionally; a negative net renders red and carries nowhere. Found by projecting the first real month-end (Aug 2026): ₹30,000 of recovery against a ₹20,000 base — ≈₹14,000 of repayment would have been recorded that no money ever paid, balances reading zero while the cash never returned. **The arithmetic was implemented faithfully; the judgment was not** — no month had ever run short before. FIX (D332 §5): capacity rule — provisional net first, recover in D250's order never past capacity, auto-defer the instalment, leave true shortfalls outstanding as explicit deferrals. | §7.1 · D332 |
| **F-148** | **S191 · CLOSED S193 (kit `S193_F6` — the bridge LIVE, built seeded-store-first per F-87; row updated at the S197 fold)** | **The drawer→ledger bridge does not exist, and the code says so honestly.** `finance_app.py` at approval: *"Approval is what posts a salary advance to the Staff Ledger. Not entry"* — then writes `ledger_posted=0, ledger_ref='PENDING_LEDGER_WIRING'`: *"B6 wires the real Staff Ledger call. Until then this records intent explicitly rather than pretending the posting happened."* B6 lived inside D329; **D330 superseded D329 whole and nothing replaced the bridge.** Every rupee drawn from the pharmacy drawer reaches the salary book only if a human types it twice; the Apr–Jun ₹40,000 still sits with `ledger_posted=0`. FIX (D332 §2.5, owner ruling): the request-not-draw flow — his entry is a REQUEST, the drawer untouched, the owner's single approval tap releases the cash AND writes the ledger row. One act, two books; the double-entry problem dissolves rather than being guarded. | §7.1 · D332 |
| **F-149** | **S191 · CLOSED S192 (kit `S192_SL7` — answered by making perks READABLE)** | **The perks-recovery route is unreachable.** D250: two skips per FY, *"3rd onward auto-flags recovery from perks."* The machine hard-refuses a 3rd skip instead (`SKIPS_PER_FY` limit raises), so the flag can never fire and the ₹19,000 sitting in his perks record can never be reached by the route the ruling built for it. Superseded in shape by D332 §2.1: DEFER replaces SKIP, first 2/FY free, 3rd onward a ₹1,000 WAIVABLE penalty on interest-bearing loans only — attached to the instrument, never the person. | §7.1 · D332 |
| **F-150** | **S191 · CLOSED S192 (kit `S192_SL5` — `attendance_enforce_from`)** | **A policy start-date that lived only in narrative was missed by the machine that had to obey it.** D249/D251 (S151), stated twice: July 2026 is pre-policy, its Deduction/Incentive columns *"PREVIEW ONLY (policy starts August)"*. The live July salary applied both anyway — **₹16,552.38 over-deducted across all twelve staff** (Darpan alone ₹3,933) — because the start-date existed only as sentences in a session record; nothing in `staff_ledger.py` or the report layer knew of it. **F-134's shape one layer up: narrative is not procedure, and it is not configuration either.** FIX: enforcement dates as SETTINGS (notice-served date unlocks enforcement; ladder rungs dated; Sunday policy the same) — shiftable by the owner without touching code. Remediation: the July sheet (per-rules column) + the owner's waiver pass; August ruled preview-only too. | §7.1 · D332 |
| **F-151** | **S191 · CLOSED S192 (kit `S192_SL5` — "attendance deduction")** | **The live system says the word the ruling prohibits.** D250 (statutory caution): deductions are *"attendance-based half-days, never 'fines'"*. The live salary table's column header reads **"-fines"** and the salary page's help text reads *"Rs 50 fine on an absence"*. Found while transcribing the live table for the July sheet — the prohibited word is in the artefact the staff see. Wording fix, no arithmetic: "attendance deduction" everywhere it renders. | §7.1 · D332 |
| **F-152** | **S192 · CLOSED same session** | **The files that GATE an install were never given the install's own line-ending discipline.** `.gitattributes` pinned `*.py`/`*.sh`/`*.html`/`*.new`/`*.sql` to LF but never `*.txt` or `*.md5` — the extensions carrying a kit's checksums and identity, and `live_pins.txt`. A CRLF `SUMS.md5` makes `md5sum -c` read the filename as `staff_ledger_X.py\r`, fail to find it, and refuse a **perfectly good kit** at gate [1/6] — a gate firing wrongly, which D316 rules is worse than no gate. Nothing had broken: **the publish warning was the finding.** Fixed same session, reasoning written into the file. | **§7.1** |
| **F-153** | **S192 · CLOSED S193 (kit `S193_F6` — `make_contra` stamps `against_month`; row updated at the S197 fold)** | **A contra does not carry the original's attribution.** `make_contra` copies category, staff, dates and the negated amount but not `against_month`, so the original keeps counting and the contra does not — a reversed advance eats its month's quota for ever. Measured: Darpan's August would have read **₹35,000 against a ₹10,000 ceiling**. Worked around by stamping `against_month` onto each contra in the correction script; **the gap in `make_contra` is still open.** | **§7.1** |
| **F-154** | **S192 · CLOSED by practice** | **The assistant had a live bridge to the owner's machine and made him do the work by hand.** A kit was delivered as a chat download with unzip instructions; it failed three times, once because the instruction carried a literal `…/` placeholder pasted verbatim as a path, once because the zip was never downloaded (git and the VPS both reported the truth). Written straight into the repo through the bridge, every later kit landed first time. **RULE: check whether a connected capability already does it before asking the owner to do it by hand — and never ship an ellipsis into a terminal.** | **§7.1** |
| **F-155** | **S193 · CLOSED same session (kit `S193_F155`)** | **"✓ applied" while the day had no ingested bills.** A Marg push reported applied when its payload had been consumed without a single bill linking (the day was not yet filed); 17-Aug read applied with empty books. Now a run is applied ⟺ **every day it carries actually ingested**; otherwise it stays `pending` with its payload kept for replay. The S194 auto-replay (`_replay_pending_marg_for_day()`) then closed the class going forward. *(F-155 was the canonical next-free at S192; S193 consumed it while the canon was unfolded — the fork this began is reconciled at v2.33, below.)* | **§7.1** |
| **F-156** | **S193 · CLOSED same session (kit `S193_STALE`)** | **A flag written at push time was never cleared.** `MARG_DAY_NOT_FILED` stayed on 17-Aug after its books filled. The Hub note now hides any such flag for a day that has a Marg batch — display-only, self-healing, no row deleted. | **§7.1** |
| **F-157** | **S193 · CLOSED same session (kit `S193_CASHPOS`)** | **The custody box showed empty from the day it shipped.** `/finance/api/custody` returned balances as comma-formatted strings; the client's `x.held>0` became `NaN>0` and every hand filtered out. Parse to number for maths, format for display — *read the payload's type before comparing it.* | **§7.1** |
| **F-158** | **S193 · CLOSED same session (kit `S193_CASHPOS2`)** | **A derived figure applied outside its valid window.** Day-wise drawer subtracted the CURRENT reserve from every historical closing → false negatives back to mid-July, before the reserve existed. The window now starts at the last clearing (`MAX(cash_custody_event.event_date)`). | **§7.1** |
| **F-159** | **S193 · CLOSED same session (kit `S193_CASHPOS3`; assistant delivery fault, recorded not silent)** | **A correct server fix looked broken for two rounds because Chrome served a CACHED API GET.** Cookie-clearing does not touch the HTTP cache. Any JSON the UI must show fresh is fetched cache-busted (`?_=<ts>` + `{cache:"no-store"}`); the server was verified directly in the owner's own Chrome before reshipping. *The browser is part of the system.* | **§7.1** |
| **F-160** | **S196 · CLOSED same hour** | **A kit delivered OUTSIDE the git tree.** The publish destination was assumed from the connected-folder root (`D:\dr-manoj-git\`) instead of read from `PUBLISH_ALL.bat`'s own `REPO_DIR` (one level deeper) — PUBLISH pushed without the kit and the VPS pull had nothing. Remedied same hour by `mv` + full re-hash, byte-identical. F-135/F-141 family: **the publish destination is read from the publisher's config, never assumed from a folder root.** | **§7.1** |
| **F-161** | **S196 · CLOSED (kit `S196_HLT2`)** | **A capability without its wire is a claim.** `_health_headline()` was built at S195 *"for the portal tile"* and consumed by NOTHING — page red, tile innocent, for a whole session. Found by reading the live bytes on the owner's "is it all taken care of?" question. Closed: `tile-summary` carries `health_line`; the Sanjeevni tile shows the worst problem FIRST. **Grep for the CONSUMER, not the definition.** | **§7.1** |
| **F-162** | **S196 · CLOSED (kit `S196_HLT3`)** | **Both A4 health cards were dead for a whole session while rendering politely.** `_health_state`'s local `today = dt.date.today()` shadowed the module `today()`; both month-vs-Marg cards died into their `except` on every render since S195 — and the S195 close had recorded the check as done. Caught by the OWNER's first real read of the page (F-132 pattern). One-line fix + a **class-refusing smoke check**: no health card may ever be a swallowed exception. | **§7.1** |
| **F-163** | **S194 · CLOSED same session (recorded at S194 as an "F-160 candidate"; MINTED at the S197 fold — see the v2.33 note)** | **The agent fetched everything and filtered, instead of searching for what it wanted.** The email query agent's first cut searched all UNSEEN and fetched **1,103 full messages per poll** — safe (it never touched them) but slow and a Gmail-load risk. Fixed by narrowing the IMAP SEARCH server-side to `UNSEEN SUBJECT "Q:"`. **Search server-side for the thing you want; don't fetch everything and filter.** | **§7.1** |
| **F-164** | **S195 · CLOSED same session (recorded unnumbered at S195; minted at the S197 fold)** | **The credit-note sign was counted twice in 2 of 3 readers** → the 18-Aug "23,879" phantom that nearly reversed a correct correction. Fixed: one `marg_net_sql()` authority used by all three. Full doc: `S195_Credit_Note_Sign_Fault.md`. **One arithmetic, one author.** | **§7.1** |
| **F-165** | **S195 · CLOSED as standing rule + tools (minted at the S197 fold)** | **Five rollbacks, one root habit: asserting against shapes not printed** — an invented fixture, guessed JSON, a self-matching search string, reserved `$args`, a mis-diagnosed encoding. Remedy adopted and tooled: `pyflakes` + `tools/check_late_locals.py` + `tools/check_row_keys.py` run before packaging ANY kit. **Never assert against an unprinted shape.** | **§7.1** |
| **F-166** | **S195 · CLOSED (coverage witness live; minted at the S197 fold)** | **A clean checklist meant NO BANK DATA, not agreement** — the monitor had statements for 8 of 90 days and reported quiet. D166/F-99's zero-anchor lesson in a new domain. The health page's UPI-evidence line is now the coverage witness: absence of evidence renders as absence, never as a pass. | **§7.1** |
| **F-167** | **S195 · CLOSED by standard (minted at the S197 fold)** | **The medical PC has no system Python** — `python` resolves to a Microsoft Store stub; every install path that assumed an interpreter failed in turn. Standard adopted: **bundled portable Python, full paths, never a system install** (the watcher ships `pyportable`; autostart via the Startup folder). | **§7.1** |
| **F-168** | **S195 · OPEN (owner path chosen: Drive-for-Desktop on the medical PC; minted at the S197 fold)** | **Every "push to medical" feature assumed a write the OS forbids** — manojz's share of the medical PC is read-only, so the ToMedical pipe never could have worked as designed (`S195_ToMedical_Pipe_Broken.md`). Owner ruling: install Google Drive for Desktop on the medical PC, making ToMedical a mounted-drive LOCAL copy (`Drive:ToMedical → D:\SendToClinic\FROM_CLINIC`); the medical-side puller build DROPPED. Open until installed. **Survey the permission before designing the write.** | **§7.1** |

| **F-169** | **S197 · CLOSED same hour (Register v5.42, the record corrected FROM the box)** | **The fold missed a pin move its own filed source carried.** `S193_UX` patched `finance_entry.html` in place (`bae2dd89…` → `92477b06…`) and recorded it in `S193_F6_Live_Pin_Record.md`; the S197 fold filed that very doc yet transcribed the file's pin from the S190 row. The first `verify_live_pins.py` run went RED on exactly this file — the F-97 chain working on its first opportunity; the box's measured value equals the S193 record exactly. F-45/F-102/F-118 family. **RULE: a multi-session fold extracts pin moves from each session's pin tables programmatically (grep the was→now tables), never by narrative reading — a fold is a transcription job, and transcription is checked by machine.** | **§7.1** |

| **F-170** | **S198 · CLOSED same session (installer v3)** | **An installer probe's expected HTTP code was asserted from assumption and rolled back a healthy install.** The `S198_P1` v2 probe demanded 200/302 from `127.0.0.1:8090`; the box answers **301** to plain HTTP for old and new bytes alike (the S196 installer had only printed it). Rule: **a probe's expected code is measured on the box or it is printed, never judged.** The F-106 family inside an installer; serves-proof moved to the app render path (importlib + `test_client`). |
| **F-171** | **S198 · CLOSED (kit `S198_H2`)** | **The health page claimed worst-first ordering it never performed** — the docstring promised the sort, no `sort` call existed, live since S195; found by the owner's eyes, not by any harness. The F-45 family (a claim outliving its implementation) in code. Fixed: `checks.sort` genuinely worst-first + the culprits named in the hero. |
| **F-172** | **S198 · CLOSED (kit `S198_H2`)** | **A Sunday-blind age check raised "Something is wrong" on a fully-filed system** — the Marg-push age counted calendar days across a Sunday the clinic does not file. A false alarm teaches staff to ignore red (the F-121 wolf-cry class). Fixed: `_sundays_between`; age checks count only expected-activity days. |
| **F-173** | **S198 · OPEN — owner review owed** | **The April-2025 NEFT advice file carries its account-number column SHIFTED against its name column** — payments that month may have gone to wrong accounts. Surfaced by the B1 transcription pass (18/18 file totals otherwise matched). Action: owner checks the April-2025 bank statement against `NEFT_Vendor_Master_v1.xlsx`; if a wrong-account payment is confirmed, it becomes its own incident. |
| **F-174** | **S199 · CLOSED (kit `S199_SALFIX`)** | **The ledger's `SALARY_EXCLUDED` grew at S192 and the salary engine's mirrored copy was never swept** — D332/SL6 added the ₹0 markers `ADVANCE_DEFER`/`CAPACITY_HOLD`; the engine's import-time drift guard (built for exactly this) refused and blanked the net/shadow columns, latent until the first live salary view. Fixed: the mirror re-aligned; guard passes. RULE: **when a mirrored rule set grows, the fold sweeps the mirrors.** |
| **F-175** | **S199 · CLOSED (kit `S199_FLOW1` + `migrate_dress_S199`)** | **An unlabeled checkbox stored money with inverted meaning** — the register's dress/I-card columns said only "Dress"/"I-card"; the DB stored a tick as a FAULT while reception ticked to mean "OK". August: 88 dress + 74 I-card phantom fault-days, the best-attendance staff ticked most. Owner ruled ticks = Yes; UI → explicit Yes/No dropdowns (only "No" stores 1); August flags migrated to 0 with a DB backup. RULE: **a boolean input's polarity lives in its label; money never hangs on an unlabeled checkbox.** |
| **F-176** | **S199 · CLOSED (kit `S199_FLOW2`)** | **Month-to-date attendance counted the RUNNING day** — a 06:00 preview showed all twelve staff absent for "today" (owner-caught on the first Sheet-1 look). Cutoff is now yesterday throughout the flow engine. RULE: **a live view of an unfinished period excludes the unfinished unit.** |
| **F-177** | **S199 · CLOSED (kit `S199_SCEN3`)** | **The scenario page labeled every month's slab columns "AUG"/"STRICT" and silently applied the strict slab to July, omitting the extra-leaves component** — compounded by a numeric coincidence (one staffer's marks money exactly equalled her old-model leave figure) that misled the owner's reading of the July page. Fixed: month-aware labels + full components (v2). The F-132 family: **a label is a claim; label from the computed value, never the assumed month.** |

| **F-178** | **S200 · OPEN — build queued** | **The mid-duty punch blindsight.** Every punch is kept, but the day computation uses only `first` and `last`, so 09:00-in / 11:00-out / 15:00-in / 18:00-out reads as a punctual full day; no screen renders the punch sequence, so it cannot be noticed. *(This index row was MISSING until v2.38 — the S200 close wrote the §7.1 entry and the changelog row but never extended the index. **F-108's exact shape, in the register that mints it.** Supplied here, recorded not silently.)* |
| **F-179** | **S201 · CLOSED (`marg_gate.py` on manojz)** | **A queue with no consumer.** `marg_router.py` stamped every verified report "queued for upload" into `_outbox` and **nothing ever read `_outbox`** — the only uploader was a manual double-click on the medical PC, last pressed three days earlier. Eleven verified reports (2 purchase · 6 closing stock · 2 expiry · 1 scrap) sat correct, hashed and undelivered while every component reported success; the sole symptom was an empty page. RULE: **a queue with no consumer is not a queue, it is a hole — assert the drain, not the enqueue.** |
| **F-180** | **S201 · CLOSED (agent S201.11)** | **The supervisor could drift silently, and did.** `medical_agent.py` S201.10 sat on Drive from 19:30 while **S201.9 kept running**; the heartbeat printed the running version with **nothing to compare it to**. The agent updates the kit but deliberately never updates itself (a supervisor that overwrites its own running file can leave the PC with no watcher) — correct, and kept. Fixed by making it **report** its own drift: each heartbeat hashes the running file against the Drive copy and prints the fix path. RULE: **a component that must not self-update must self-report; compare by md5, never by the version string a file claims about itself (D188).** |
| **F-181** | **S201 · CLOSED (kit `S201_UI`)** | **Nested `<a>` broke a health row, and every counting test passed.** The Correction-checklist row was wrapped in `<a class=row>` while its hint carried a second anchor inside it; nested `<a>` is invalid and every browser un-nests it, orphaning the status mark and dropping `.body` outside the row. The S198 tests counted rows and counted clickable rows — **both counts stayed correct; only the SHAPE was wrong, and no assertion described shape.** Found in the owner's own saved copy of the SERVED bytes (the second time in one session). Fixed: a linked row strips anchors from its hint; asserted on the served bytes that no row anchor contains another. RULE: **when a count is right but the shape is wrong, no counting test will see it — assert something the change did not preserve.** |
| **F-182** | **S201 · CLOSED (kit `S201_UI`)** | **`/finance/health` was in no design register at all.** The F-130 `_DESIGN_V1_PAGES` table asserts pre-v1 pages *negatively* so a page cannot change design class silently — but this page was never listed, so it was neither protected nor recorded, and sat on pre-v1 styling for fourteen sessions with nothing noticing. F-107's absence-blindness, one register over. Fixed: registered `True`. RULE: **a register that only checks what it lists must be asked, separately, what it does not list.** |
| **F-183** | **S201 · OPEN by choice — own kit queued** | **Two latent faults in the clinic-ID attribution rule.** (a) The `0.60` tier parks a bill that HAS a clinic ID but no name — **backwards**, since the ID is the strongest identifier available. (b) The pattern `[A-Za-z]{0,3}\d{2,8}` requires two or more digits, so **single-digit clinic IDs would not match** (the clinic's numbering started at 1). Neither occurs in the 192 bills measured across seven days. Deliberately excluded from `S201_HEALTH` and `S201_UI`: **mixing a behaviour change into a labelling and a drawing fix makes a rollback hard to reason about.** |

| **F-184** | **S202 · CLOSED in the artefacts · routine fix OWED at the close** | **`deploy_kits/KB_canon_all/` — the folder Phase 0 verifies — has never been maintained by any numbered step.** Three instances, one root: the pin checker could only return AMBER because the close filed its canon into a per-close folder it never looks in (reserved at S201); `MD5SUMS_ALL.txt` was four sessions stale with **24 files present-but-unlisted** and exited on a WARNING (**F-119** = FAIL); and **twelve manifest-pinned canonical documents were absent from the folder entirely**, so the one mechanical Phase-0 command verified a subset and reported OK. `KIT_ID.txt` disagreed with the checksum file it exists to carry. **The folder's own `README_VERIFY.md` already specifies the inverse check — nothing ran it.** Repaired at the S202 open; `END_OF_SESSION_PROMPT` **v8 step A8b** owed at the close. |

| **F-185** | **S202 · CORRECTED AT THE CLOSE · OPEN — owner re-ruling of D320 owed; worst files quarantined same hour** | **The public repository carries real patient data, including named patients with their diagnoses — and the decision to keep it public was made on a count that was wrong by about nineteen times.** F-96 recorded 7 mobiles / 2 names / 1 clinic ID across 48 files; measurement found **133 distinct mobile-shaped numbers across ~190 files**, plus **13 named patients with age, sex, mobile, DIAGNOSIS and comorbidities** in two orphan sample files, 38 real caller numbers in a one-off script, and name+mobile+clinic-ID fixtures in three copies of `marg_report.py`. F-96 only ever examined the canonical DOCUMENT set — never code, never test data. The three orphan files (referenced by nothing, verified before moving) are **quarantined, not deleted**; the live parser fixtures are deliberately untouched. **Moving files forward does not remove them from past commits — only making the repository private removes public reach to history.** `tools/phi_scan.py` + `PHI_SCAN.bat` now gate every publish; first run: **271 files awaiting triage.** RULE: **a ruling inherits the reliability of the facts it was given.** | ⚠ **CORRECTED 26-Aug-2026, struck through rather than deleted (F-23). THE CENTRAL CLAIM WAS FALSE.** The assistant reported 13 named patients WITH DIAGNOSES exposed in the public repository. **They were never public.** `.gitignore` line 31 (`*.csv`) had always excluded them and **not one `.csv` is tracked in the entire repo** — `git log` shows they were never committed. The scanner **walked the FILESYSTEM instead of asking git what is public**, so it saw files git was deliberately holding back and called them exposed. Measured against `git ls-files`: **62 distinct mobile-shaped numbers, no diagnoses, ever** — the two largest sources synthetic fixtures. **F-96 was right all along, at roughly ten times its recorded count, without the category that made it alarming.** The scanner now REFUSES to run if it cannot ask git, rather than falling back to a filesystem walk. **The urgency the assistant attached to making the repo private was built on this error.**
| **F-186** | **S202 · CLOSED (record corrected from the box) · structural gap OPEN** | **The live-pin discipline reaches only the VPS, and a real PC-side drift sat unseen.** `margpull/signatures.json` on manojz was `3e9cbba0…` against a Register pin of `1b21f3bf…`, changed during S201 and never recorded — **F-97's condition on the one file class `verify_live_pins.py` structurally cannot check.** Diffed rather than assumed: nothing removed, four types gained an `end_marker` each stamped *"S201: verified from a real sample"*, one new `STOCK_CLOSING` variant added — **the live file was better than the record.** Corrected FROM the box (F-169 precedent), repo mirror synced, previous bytes kept as `.bak_S202_1b21f3bf`. The checker's own words on such rows — *"blind spots, not passes"* — were accurate. **Structural fix = B2 / PC-side pins; second instance after the two-builds-stale medical parser.** |

| **F-187** | **S202 · CLOSED (kit `S202_DARPAN20K`)** | **A custody fact recorded in prose, where no query could reach it.** On 17-Aug Darpan's drawer was cleared; `cash_count.explanation` itemises it in words — *10,000 July advance + 20,000 August advance + 18,963 to the owner*. The 18,963 became a custody event, the 10,000 an expense; **the 20,000 became nothing**, so every drawer figure from 17-Aug carried money the drawer did not hold. **F-137's exact shape.** Settled by PHYSICAL COUNT: books 63,903, drawer 43,903, difference 20,000 to the rupee — and the prior theory (*20,003 with 3 written off*) was DISPROVED first, 20,003 being a running balance that reconciles on every row. Stamped `ledger_posted=1` against SPECIAL `0cc0b26b38c5` so approval cannot post a second Rs 20,000. **RULE: a count is evidence; a theory that fits two digits is not.** |

| **F-188** | **S202 · CLOSED (kit `S202_D349A` v2)** | **F-106 RECURRING: a self-test that asserts a DATA STATE becomes a liability the instant the data is legitimately corrected.** Three D330 ceiling checks built their fixture from the live store, assuming the month's advances leave room under Darpan's Rs 15,000 ceiling. F-187's correction — money proven by a physical count — put August over it, `_room_p` went negative, the test posted a negative rupee amount and the endpoint rightly answered `not_a_number`. **The books were correct and the TEST was wrong.** Reproduced offline on the UNPATCHED app (645 → 642) before anything changed, then made state-adaptive with 3 checks in both branches. Same remedy as `S184_F1b`, eighteen sessions later. |

| **F-189** | **S202 · CLOSED (assistant fault · three instances in one day)** | **GATES THAT DO NOT GATE.** (a) `S202_DARPAN20K`'s smoke gate read `grep -qiE "([0-9]+)/\1|all .*pass|OK"` — case-insensitive with a bare `OK`, matching almost any output; **verified to accept 642/693**, so it passed a degraded suite that a different kit's exact-count gate caught an hour later. (b) The same kit's preflight demanded the `sqlite3` BINARY it never invokes — a **false refusal of a correct kit**. (c) The pin-list generator was run with `2>/dev/null`; **it refused, correctly, and the refusal was silenced** — the stale pin list survived and was almost reported as freshly generated. **RULE: a gate is written by asking what it must PROVE, never by copying a previous kit's shape — and a gate's refusal is never redirected to /dev/null.** |

| **F-190** | **S202 · CLOSED (`.gitattributes`)** | **192 of the 208 files in the canon folder were free to change their own md5 on checkout.** `.gitattributes` pinned `*.py *.sh *.html *.new *.sql *.md5 *.txt` to LF and **never `*.md`** — and the entire canonical set is `.md`. Under git's **Windows default** (`core.autocrlf=true`) every one checks out CRLF and every hash changes; demonstrated on the live Register, `3ed8c494…` → `81e54f4d…`. **Phase 0 would go RED on all 192 at once.** It never bit only because manojz happens to have `autocrlf=false` — one machine-local setting nothing records or checks. **THAT IS THE DISASTER-RECOVERY CASE**: the cold kit exists so the canon can be restored, and restored onto a default Windows machine it would fail its own verification entirely. D164 stopped at `.py/.sh`; F-152 added `.md5/.txt`; **neither asked WHAT ELSE IS UNPINNED** — F-107's shape applied to file classes. |

| **F-191** | **S202 · two instances CLOSED · the eleven-month one is the OWNER'S to close** | **MONITORS BORN DEAD — configured, never confirmed producing output, silently useless.** (a) `pipeline_status.py` was wired into `PULL_FROM_MEDICAL.bat` **after** the early exit for an unreachable medical PC, so **the monitor ran only when the pull SUCCEEDED** — it could report success and nothing else. Built the same morning as the never-fired witness designed to catch exactly this, and wired past it. (b) B2A's own smoke gate — see F-189. (c) **`E:\auto` and `E:\MARGBCKUP\auto` on the medical PC have been EMPTY for eleven months**: automatic Marg backups were configured around 02-Oct-2025 and have never once run, while a human filled the gap manually every 2–4 days. **RULE: a facility that is configured but never confirmed producing output is not configured — it is decoration.** AF-2 was the same shape and showed green for five sessions. |

| **F-192** | **S202 · CLOSED (kits `S202_B2C`, `S202_PICTURE`)** | **A STALE READING REPORTED AS A LIVE STATE — the false green.** (a) B2A's watcher check read `alive` straight from the payload, but that value comes from a heartbeat FILE which stops changing when the medical PC is switched off — still saying ALIVE. **It showed a green light for a machine that was off, and would have every night.** Now gated on the heartbeat's AGE. (b) `MARG_PICTURE.txt` measured coverage from the earliest report EVER SEEN, so one deliberately-generated 12-June report made it claim **56 MISSING DAYS** where the day before it read 0. Windowing alone still claimed 32; the machine now **does not guess when coverage began** — it is told, in `_coverage_from.txt`. **56 false alarms became one real one (25-Aug).** **RULE: a false GREEN is worse than a false red, and a false alarm every ten minutes is how a file stops being read.** |

| **F-193** | **S202 · CLOSED (documented by symptom)** | **ERROR MESSAGES THAT NAME THE WRONG CAUSE — three in one day, costing about an hour.** (a) The pull printed *"Is it switched on and Tailscale connected?"* while the PC was on, the owner was in an RDP session with it, and Tailscale showed it `active; direct`. (b) Windows blocked the share to protect against *"unsafe or malicious devices"* — a credential problem. (c) Marg answered *"Few important files not found in SYSTEM / Please RE-INSTALL software!"* because it was launched with the wrong working directory — **an instruction to reinstall an ERP on a live pharmacy system, for a `cd`.** The pull now pings first and says WHICH; the other two are documented by symptom in the maintenance flow. **RULE: an error must not list only the causes it cannot tell apart. If it can distinguish them it must; if it cannot, it must say so rather than guess.** |

| **F-194** | **S203 · CLOSED (the B2 gate fix, then the B2 test)** | **A ROUTE THAT WAS NEVER ADDED TO THE LIST THAT LETS IT IN — B2 had never once reported.** `_gate()` is a `before_request` that fails closed and exempts exactly three literal paths: the cron token (any path), `MARG_TOKEN` for `/finance/api/marg-push`, `RENEWALS_TOKEN` for `/finance/api/renewals-push`. **`/finance/api/pipeline-status` was added at S202 and never added to that list**, so every real post was refused **before** `api_pipeline_status()` ran and the route's own token check was unreachable dead code. Proven both ways on the box: a POST from the VPS with the server's own `FINANCE_MARG_TOKEN` returned **401 `not_signed_in`** before and **HTTP 200 `{"ok":true,"received_at":"2026-08-26T18:52:00"}`** after — then proven again from the **REAL caller**, three consecutive `pipeline_status: 200 (token from medical PC (live))` including the scheduled 19:10 and 19:17 runs. **Third instance of AF-2's shape: a monitor born dead.** `finance_app.py` `50ac4c86…` → `374a0b82…` → **`7948cee0…`**. **RULE: adding a route that carries a token is not finished until the gate in front of it has been told, and the proof is a call from the real caller, not from a curl.** |

| **F-195** | **S203 · OPEN (assistant fault · the fix does not bite)** | **BOTH CHECKS PASSED FOR REASONS OTHER THAN THE ONES THEY NAME — and so does the check written to fix them.** The smoke suite *does* post to `/finance/api/pipeline-status` with the `X-Finance-Marg` header, but on `c`, a **signed-in** test client: `_gate()` waved it through on the **session**, so the token clause was never exercised at all. The check immediately above it, *"an unauthenticated pipeline post is REFUSED"*, returned its 401 from the **route's** check rather than from the gate. The token substitution is only half applied — the test sets `os.environ["FINANCE_MARG_TOKEN"]` while `_gate()` reads the module-level `MARG_TOKEN`, **bound at import**. **And the two checks added at S203 to close this DO NOT BITE: reverting the gate still gives 721/721.** Recorded here as green-and-meaningless rather than left standing as coverage — the honest thing and the uncomfortable one. **RULE: a check must be run against the broken state before it is trusted; a check that cannot go red has measured nothing.** F-106/F-142's family, and the second time this session (see F-198's red-proof, which was done properly). |

| **F-196** | **S203 · CLOSED (kit `S203_R2`)** | **A SUCCESS WORD WRITTEN UNCONDITIONALLY, AND THEN RELAYED AS LIVENESS.** `PULL_FROM_MEDICAL.bat` wrote `-- ok` whatever had happened, and `pipeline_status.py:122` carries that exact word to the clinic server as evidence the leg is alive. Now every step's exit code is checked and **the word is earned**. `92f03999…` → **`cfb8b13d…`**. **RULE: a status word is a measurement or it is a decoration — never a constant.** F-192's false-green family, one layer further out. |

| **F-197** | **S203 · CLOSED (kit `S203_R2`)** | **THE PULL KEPT NO LOG AT ALL.** `PULL_HIDDEN.vbs` ran the pull every ten minutes and discarded stdout, so nothing the chain said had ever been retained. **This is the finding that made the other two findable**: the log arrived at 18:38 and the 401 that had printed on every pull since S202 was legible six minutes later. Now `_logs\pull_YYYY-MM.log` and `_logs\pull_console_YYYY-MM.log` exist. `9a3ba9ba…` → **`084fc452…`**. **RULE: a scheduled job that discards its own output cannot be diagnosed, only guessed at — and the first fix in any dark leg is a log, not a theory.** |

| **F-198** | **S203 · CLOSED (kit `S203_R1`)** | **AN UNREADABLE FILE VANISHED, AND WAS RE-REFUSED FOR EVER.** `marg_router.py` refused an unreadable `.xls` **above** the archive-and-index block, so it was never copied to `_REFUSED`, never written to `index.csv` and — because `seen` is rebuilt from `index.csv` on every run — **re-refused every ten minutes indefinitely**, with the only message going to the console F-197 was discarding. Fixed by lifting the tail into `_archive_and_index()`, called by **both** paths. Selftest **14 → 21, +7 exactly**, and the seven were run against the **unfixed** file first: **five go RED**, the two that pass were already true. `bbc50f91…` → **`781e5ff6…`**. **RULE: a refusal path must archive and index exactly like an acceptance path, or the refusal is a deletion with a log line.** |

| **F-199** | **S203 · CLOSED by measurement** | **THE MIRROR IS NOT EVIDENCE OF WHAT IS ON THE MACHINE.** manojz's copy of the medical PC is `robocopy /E` with **no `/PURGE`**: it has never deleted anything, so it still showed **340 `marg_watch.py.before_*` files** (the agent prunes to 3, and exactly 3 are there), an AutoHotkey install with its export macros, and `GUARD_AND_SEND.bat`, `guard_and_send.py`, `marg_report.py`, `INSTALL_WATCHER.bat`, `START_MARG_WATCHER.bat` and `xlrd\` — **none of which the machine's own 77-file listing contains**. Every statement made about that PC from the mirror was a statement about its history. **RULE: reasoning about a machine from a non-purging mirror is unsafe; ask the machine.** This is why the pins in F-200's neighbour section were taken, and it is the direct cause of F-206. |

| **F-200** | **S203 · OPEN (an inverse check across stores is owed)** | **PROJECT KNOWLEDGE WAS THE STALE STORE, NOT THE REPO.** Two documents exist in both stores and are **not byte-identical**, and in **both** cases the **repo** copy is the better one, carrying superseding annotations written at the S197 fold that never travelled back to project knowledge. **The four lines missing from the project copy of the encryption note are exactly the warning that would have prevented the S203 master reference asserting a superseded finding as current.** The habit this corrects is positional: project knowledge had been treated as the live store and the repo as the archive, and it was the other way round. **RULE: neither store is authoritative by position — compare by md5, never by where a file sits.** D188 applied to stores instead of filenames. **OPEN: the inverse check — every document in each store compared against the other — has not been run.** |

| **F-201** | **S203 · CLOSED by measurement (and the assistant's first verdict on it was also wrong)** | **F-191(c) WAS WRONG: THE BACKUP WAS NEVER SCHEDULED.** F-191(c) recorded that the automatic Marg backup *"was configured and has never once run."* Measured on the machine: **six non-Microsoft scheduled tasks, all Google and OneDrive**; nothing at startup runs a backup; **115 Marg config files and not one mentions backup**. **It was never scheduled. The empty `auto` folders were never going to fill**, and eleven months were spent waiting for a mechanism that did not exist. Also measured: `E:` **28.5 GB free of 28.9**, **177 files / 0.4 GB**, newest **22-Aug**; `E:\MARGBCKUP` last written **09-Oct-2025**; `margwin.exe` running (pid 7172) so `D:\MARGERP\Data` (**1,075 files, 0.9 GB**) is open FoxPro tables; the **previous financial year last backed up 17-Jul**, one copy. Marg's own `serverbackup` is no substitute — the real ~2.3 MB `*_c18_d_*` pair exists only for 26, 25 and 22-Aug, then a **12-day gap** to 10-Aug, and it sits on **D:, the same disk as the data**. **(b) ASSISTANT FAULT, same subject:** the first verdict built on this measurement announced *"the backup target is NOT ATTACHED"* while the same report said **"E: is present"** — a **shadowed variable**, and a report that contradicted itself and was published anyway. **Fixed:** the agent now copies the stick offsite automatically, bounded to 64 MB a pass, with the backup's age in every heartbeat and a warning past three days — **proven at 19:37, `offsite: 182 file(s), 0.41 GB … offsite copy is COMPLETE`, newest backup 0.2 days old**, unattended. **STILL OPEN and stated plainly: no restore has ever been tested.** **RULE: "configured but never runs" and "never configured" are different faults with different cures — measure which one you have before writing either down.** |

| **F-202** | **S203 · OPEN (rotation parked by the owner)** | **THE TOKEN LIVES IN FIVE STORES, NOT THREE.** The record carried three copies. The machines carry five: the VPS unit, the medical PC, the manojz cache, `D:\Downloads\MARG_TOKEN_S187.txt`, and a loose file under `margsync\_to_delete\S201_20260825\loose\`. **A rotation planned against three would have left two live.** The owner has parked rotation for now, and it is parked with the correct number. **RULE: a secret's blast radius is counted on the machines, not in the record — and "to_delete" is a folder name, not a deletion.** |

| **F-203** | **S203 · CLOSED** | **THE OPERATIONAL RUNBOOK ON THE MACHINE THAT RUNS THE PULL WAS TWO SESSIONS STALE.** manojz's copy was the **S201** version (`f02cd8bd…`) and therefore **missing the guest-access fault that caused the S202 outage** — the one page a person would reach for at 07:33 with the feed dark did not contain the cause. Corrected to `c2b5251f…`. **RULE: a runbook is a live file on the machine it serves; publishing it to the canon is not delivering it.** |

| **F-204** | **S203 · CLOSED (assistant faults · two instances)** | **A PROXY TRUSTED IN PLACE OF THE THING.** (a) **A `NameError` shipped twice.** An insertion anchor matched in **two** places, and `py_compile` — the build gate this project has leaned on since S100 — **compiles an undefined name without complaint**. It cannot see the fault class it was being asked to catch. **`pyflakes` can, and is now used.** (b) **`trap … EXIT` was pasted into an interactive shell**, where it fired at the wrong moment; a **reverted file sat on disk while it was believed restored**, and the belief was not checked by hash until later. **RULE: `py_compile` proves a file parses, never that it runs — pair it with `pyflakes`; and a restore is believed only after the hash agrees.** F-142's family — a harness must prove the thing it read is the thing it claims. |

| **F-205** | **S203 · CLOSED by D351 (assistant fault)** | **THIRTEEN DOCUMENTS PRODUCED WHILE CONSOLIDATING SIXTY-NINE AWAY.** The session whose purpose was to stop the Marg/medical document set growing produced thirteen new documents in the course of doing it. Nothing was lost and nothing was wrong in them — that is not the point. **The behaviour that made sixty-nine documents was running inside the work to reduce them**, and it would have re-grown the set within a few sessions. **D351's third rule exists because of this session's own conduct, not in spite of it:** anything written to work something out is a WORKING PAPER, stamped as one **at birth**, and folded at the close. **RULE: a consolidation that emits new canonical files has not consolidated; count your own output against the thing you are shrinking.** |

| **F-206** | **S203 · OPEN · AF-1 REMAINS ARMED (the strike was proposed at this close and REFUSED)** | **A HIGH-SEVERITY FAULT WAS NEARLY STRUCK BECAUSE IT WAS FILED AGAINST THE WRONG FILENAME.** The close carried an instruction to strike **AF-1** on the ground that it is armed against `GUARD_AND_SEND.bat`, which the medical PC's own listing proves is absent (F-199), and that the fallback D347 preserves — `SEND_TO_CLINIC.bat` — is self-contained. **The second half is true; the first is not; and the conclusion does not follow.** `GUARD_AND_SEND.bat` is **88 lines**, calls `guard_and_send.py` and hands off to the sender, and **contains no `curl`, no `last_response.txt`, no `sent_hashes.txt` and no `ACCEPTED-FOR-REVIEW` test** — AF-1's mechanism was never in it. AF-1 was recorded against **`SEND_TO_CLINIC.bat`, kit `S187_M1a`**, and the live file — **`e19a8a777ac22fe75a242f1eb9762185`, a verified S203 pin on the machine now** — still carries it whole: `curl -s -m 90 -o "%RESP%"` with **no `del` of `%RESP%` beforehand**; a `findstr /c:"ACCEPTED-FOR-REVIEW" "%RESP%"` that **never consults `%HTTP%`** (captured into `last_http.txt`, and used only in the REFUSED message below it); and on the ACCEPTED branch `echo %HASH%>> "%HASHES%"`, which the skip test at the head of the routine then honours for ever. **So the sender is self-contained AND the fault is live inside it**, and a network failure still produces a printed ACCEPTED over a report that never left the PC — with the cure (deleting one line of `sent_hashes.txt`) still written nowhere. **This also opens the bridge the AF-# series never had to the F-# register.** **RULE: a fault is attached to a mechanism, not to a filename — before striking one, find the mechanism in the current bytes and prove it is gone. D188, applied to a fault instead of a document.** |

| **F-207** | **S204 · FIXED (kit `S204_C2`)** | **The file names the fault, then commits it.** At line 9886 of `finance_app.py` the smoke suite's own comment says *"a hardcoded `15,000.00` would go red the day the owner revises the base or the pct"* — and **sixteen lines below, twice, it hardcodes exactly that literal.** The block around it had been made state-adaptive deliberately (the S184_F1b remedy); the ceiling figure was left behind. Surfaced the instant **D352** made the ceiling ₹10,000: live smoke **720/721**, the failing line printing `ceiling=10,000.00`. Fixed by replacing both literals with `rupees(_want_ceil)` — the value that block already computes from the store. **RULE: a self-test that asserts a DATA STATE is a liability the moment the data is legitimately corrected, and a warning written beside the fault does not prevent the fault.** | §7.1 · Archive §S204 |
| **F-208** | **S204 · OPEN (structural) · assistant fault** | **The audit convicted on re-keyed text.** `Diagnostics_Surveillance_System_Spec_v2_3` was reported drifted between the two stores at `be2db910…`; it is **byte-identical in both** at `bdd5fa54…`, the manifest pin. The reported hash was reconstructed exactly: **the canonical document minus one contiguous 4-line block — the D114 paragraph naming this register as the authority** — dropped by the transcription itself. Fifteen copies on the machine, every cold kit and a full git object-database scan all give `bdd5fa54…`. **`S181_postclose_addendum.md` §3 had already ruled that re-keyed inline text "may corroborate, never convict and never acquit" — and the audit convicted on it anyway.** Remedy used for the preservation that followed: **two independent transcriptions, compared — 42 of 44 converged byte-for-byte**; the two JSON files did not and are recorded as fidelity-NOT-established. **Structural fix owed: the rule belongs in the close-out routine.** | §7.1 · Archive §S204 |
| **F-209** | **S204 · PARTLY CLOSED (3 of 4 captured) · `make_force_keys.py` OPEN** | **A pin is not a backup.** All 67 rows of `live_pins_S203close.txt` checked against all 1,952 repo files by hash: 61 recoverable, **four in ONE PLACE ONLY** — `/root/finance/finance_app.py` (the money application; the newest repo copy predated the S203 gate fix), `finance_entry.html` (15-Aug), `email_agent.py` (21-Aug), `make_force_keys.py` (**never**). The checker is GREEN on all four **and that is correct** — they match the record, and **the record is a hash, not the bytes**. Kit `S204_C1` captured 31 files (0 drift, 0 missing), verified twice against independent references. **`make_force_keys.py` remains single-copy** — 38 mobile-shaped strings, held back by the F-185 gate; **it cannot go into a public repo and needs a home that is not git.** | §7.1 · Archive §S204 |
| **F-210** | **S204 · OPEN · documented in the capture manifest** | **The executable bit does not survive VPS → tarball → Windows → git.** git's own words: `mode change 100755 => 100644` on `email_agent.py` and `finance_backup.sh`. Bytes identical, mode lost. **`finance_backup.sh` is a shell script: restored from the repo it will not run.** A hash cannot carry a permission, and the pin list records neither mode nor ownership — **so a rebuild that verifies GREEN on every hash can still produce a backup script that silently never runs.** Restore lines carrying `chmod +x` added to `deploy_kits/S204_VPS_LIVE/MANIFEST.md`. Found only because a guard refused to proceed on a difference it could not explain. | §7.1 · Archive §S204 |
| **F-211** | **S204 · OPEN · owner rulings owed** | **The two document stores disagree in BOTH directions.** 156 documents compared: 102 identical · **5 stale in project knowledge**, including **`S190_Staff_Advance_Policy_D331`, which project knowledge shows as a DESIGN draft "awaiting the owner's OK" while the repo and the manifest pin carry SIGNED AND EXECUTED** · **1 stale in the repo** (`OWNER_TODO_LIVE`, by design) · **1 three-way fork** (`S196_Health_Renewals_Build_State` — the S197-fold copy silently dropped the F-155 clause while adding its own marker; **no correct copy exists anywhere**, F-23's shape) · **45 present only in project knowledge** (44 preserved to disk; the `.docx` could not be, and remains single-copy). **RULE: the reconciliation rule is NOT "keep the superset"** — that would have destroyed the S203 `OWNER_TODO_LIVE`, which has none. Per-document direction check. **And the repo copy is not automatically right either: the S190 policy is stale in BOTH stores against the deployed code (SL3/SL4).** | §7.1 · Archive §S204 |
| **F-212** | **S204 · FIXED in the method · assistant fault** | **Two publishers, one repo, and no rule about which one publishes.** The VPS committed the capture locally (its push correctly refused — no credentials on that box, by design), and the same content was then published from manojz. The histories **diverged**, `git pull --ff-only` refused, and the next kit's delivery failed with *"No such file or directory"* — **a message that named the symptom, not the cause.** Fixed by a self-guarding block that proved origin carried identical content before discarding the box's local commit; the guard then fired twice more, correctly, on an untracked stray and on the mode difference that became **F-210**. **RULE: one repo has one publisher. Any other box is a delivery channel, and a delivery channel must not commit.** | §7.1 · Archive §S204 |

*Next free finding: **F-218**.* *(F-213 … F-217 appended at the S205 close — see §7.1 (continued) — S205.)* *(Advanced from F-194 at v2.42 together with the index rows above, which end at F-206 — the §2-item-9 agreement check this register prescribes, and the F-45/F-108 family it exists to catch.)* *(This line read "F-115" through v2.20 and v2.21 while the index rows above it were current — the F-45/F-108 family; corrected at v2.22, not silently, and advanced with the index ever since. It then read "F-155" for four sessions while S193–S196 minted through F-168 in standalone docs — the same family at register scale; reconciled at the S197 fold, v2.33.)*

---

## §7.1 — FULL TEXT: F-82 … F-89

> **Why this section exists.** F-82 through F-89 arrived as three standalone **append artefacts**
> rather than as index one-liners, and they were owed to this register for nine sessions. §7's
> established pattern is *index here, full text in the Archive* — applying that pattern alone would
> have thrown away the text these appends carried. The bodies below are reproduced **verbatim** from
> the three hash-verified append files; the Archive remains the authority for the surrounding session
> narrative.
>
> Sources, all three hash-verified at the S181 Phase 0 — no filename was taken as provenance (**D188**):
> `Fault_Register_append_F82_F83_S177.md` (md5 `3393d527d7c4e65b6c0504f932babb12`, matching the
> manifest's `3393d527…` pin) · `Fault_Register_append_F84_S179.md` (md5
> `cce4009f373971fdadf8ed1f9b031d03`) · `Fault_Register_append_F85_F89_S180.md` (md5
> `80a01080c74cea66fdb8b6acf337d2ca`).

---

### F-82 (S172, OPEN — VENDOR-SIDE) — MyOperator WhatsApp Developer API returns HTTP 500 {"message":null} on ALL authenticated calls

**Symptom.** Every AUTHENTICATED call to `https://publicapi.myoperator.co` for the clinic account returns `HTTP 500` with body `{"message": null}` — reads (`GET /chat/templates`, `GET /chat/phonenumbers`) AND sends (`POST /chat/messages`). Observed identically from (a) the new portal sender `portal_wa.py` and (b) the tracker's own long-proven `wa_send.py` path, using the identical token (sha8 `d47a090a`, = tracker `WA_TOKEN`), company ID `68384350414b9847`, WABA ID `2101222617483538`, phone-number ID `1090067637530949`.

**Not our code.** An UNauthenticated call to the same endpoint correctly returns `HTTP 401` — the API is up and the token authenticates past the auth gate; only account-resolution fails. Inbound WhatsApp (webhook → `/root/wa/wa_logs/*.jsonl`) is unaffected (today's file present + populated). Two independent code paths + two different read endpoints + the send endpoint all fail identically → not a payload, header, token or portal bug. **Root cause is account-side / provisioning at MyOperator**, starting today.

**Diagnostic ladder (the reusable playbook — run in this order):**
1. `tail` the send log `/root/wa/wa_portal/wa_portal_sends.csv` for the exact error string.
2. Fingerprint the portal token vs `.env`/`wa_send.env` by **len + sha8 only** (never print the token).
3. Live-send to the doctor's OWN number via the tracker's proven `wa_send.py` path (rules out portal request-shape).
4. Do a READ call (list templates). **If a read fails too, it is not payload.**
5. Do a NO-AUTH call. **401 = API up + account not resolving (vendor); 500 everywhere = wider outage.**

**Action.** Escalated to **Khushi** (MyOperator account manager, email with full request/response detail) + **Lokesh Kumar VB** (engineer). `PORTAL_WA_DRYRUN` returned to `"1"` (SAFE). Go-live blocked pending vendor restore; when restored, flip DRYRUN→`"0"`, restart, self-send `drmanoj_post_visit` to the doctor's own number, confirm, then live — no code change.

**Lesson.** Three successive wrong diagnoses (account → config → account) were resolved only by the no-auth 401 control — **run the auth-gate control EARLY**, before theorising. Related near-miss (NOT a fault): a first install targeted `/root/wa` instead of the real portal dir `/root/portal` — caught immediately by the md5 gate; the portal is `/root/portal/portal.py`.

*Full narrative: Archive §S172. Status: OPEN (vendor).*

### F-83 (S176, OPEN — mitigated) — Asset-app intake background OCR thread is fire-and-forget

**Symptom.** The first real reception bill (B-0001, Shri Ram Enterprise, ₹1,30,003) arrived on the checker's screen BLANK although Sarvam extraction was configured and working — a later manual re-run extracted vendor, bill number, total and all 5 line items correctly.

**Root cause.** The A-D21 reception intake fires the Sarvam extract in a plain background `threading.Thread` from the request handler: fire-and-forget. The thread **dies on service restart** (an install/restart between scan and completion kills the read) and the fill deliberately **skips non-draft bills** (non-clobber), so a bill promoted or touched before the thread completes never receives its read — with no visible trace of failure.

**Mitigation shipped (A-D23, S176, LIVE):** the read is no longer silent — `ocr_status` (reading / read / empty / failed) is stamped on the draft + the Purchases list; a **"Re-read with Sarvam"** button (non-clobber, works on drafts AND approved bills) recovers any lost read; approving a bill with blank fields now requires an explicit server-enforced confirm. B-0001 was recovered via Re-read.

**Durable fix (owed, A-D25 candidate):** replace the thread with a survivable path — either a queue + worker (systemd or cron sweep over `ocr_status='reading'|'failed'` drafts) or synchronous extract with a bounded timeout at scan time. Until then, restarts of `assetapp.service` should be followed by a glance at the Purchases list for stuck "reading" badges.

**Lesson.** A background thread inside a gunicorn worker is not a job system: anything that must complete needs a durable record of "not done yet" and a path to retry — visible status first (shipped), survivable execution second (owed).

*Full narrative: Archive §S176 (fold) + `KB_Asset_Register_v1_10_3.md` §7. Status: OPEN (mitigated by A-D23); asset-app located, clinic-numbered.*

---

### F-84 — Three self-found security faults in the finance module: the offline-testing shortcut was the vulnerability (OPEN → FIXED, S179)

**Severity:** high (auth bypass reachable in production for ~2 min on an unpublicised path; header
identity was full control, not a leak). **Status:** all three FIXED and installed this session; the
installer auto-rolls-back if the epoch check fails. Recorded as a lesson to carry, not an open risk.

**Owner did not flag these — I found them after the first install, on my own review.** All three had
the **same shape:** something that made development or offline testing easier, carried into
production without asking "what does this let a stranger do?"

1. **Reads were ungated.** Identity was checked only on writes, so `/finance/api/tile`, `/month`,
   `/day` and the patient lines were readable by anyone with the URL.
   *Fixed:* a **fail-closed `before_request` gate** over an allow-list (`PUBLIC_PATHS`), so a route
   added later is protected without anyone remembering to gate it.

2. **Identity came from spoofable HTTP headers in production.** `X-Clinic-User` / `X-Clinic-Role`
   were an offline-testing convenience that reached prod; `curl -H "X-Clinic-Role: checker"` would
   have approved days and run the cutover. That is control, not a leak.
   *Fixed:* the real `clinic_sso` signed cookie is authoritative; header auth is off unless
   `FINANCE_ALLOW_HEADER_AUTH=1` (the systemd unit states in plain words why it must never be set).
   Tightened further: *signed in ≠ entitled* — a valid clinic login with **no `unit_role` row on
   `medical`** gets 403, so the manager cannot read the pharmacy's cash.

3. **The epoch was never checked.** `verify_token` ran with `current_epoch=None`, so **"Sign out
   everywhere" revoked sessions in the portal, ledger and asset app but NOT here** — a revoked token
   still opened the books. Found only because a stale epoch threw a 403 on `/portal/users` and the
   diagnosis exposed the asymmetry.
   *Fixed:* read the epoch from `clinic_users.get_epoch(clinic_users.DEFAULT_STORE)` on **every**
   request (never cached — a cached epoch keeps revoked sessions alive for the cache's life) and
   **fail closed** if it cannot be read, exactly as the portal does. `healthz` exposes
   `sso_epoch_ok` so a lockout is diagnosable without a cookie, and the installer rolls back
   automatically if that flag is false after restart.

**THE LESSON WORTH KEEPING:** *the offline testing shortcut was the vulnerability.* Anything that
grants identity for convenience must be **opt-in**, and the production default must be **closed**.

**A fourth, smaller lesson (a test defect, not a prod fault):** one install was rolled back by its
own gate because a *test asserted an environment accident* ("the epoch is unreadable here") rather
than a behaviour. Tests must assert what the code **does**, not what the machine happens to look
like. The replacement forces the epoch to be unreadable and **requires refusal** — deterministic on
any box.

**Prevention now standing:** fail-closed `before_request` allow-list on every new Flask surface;
identity only from the signed SSO cookie in prod; per-unit entitlement is the sole authority (broker
role grants nothing); epoch read live and fail-closed; `healthz` surfaces `sso_epoch_ok`; installer
gates on it. Extends F-63 (route-gate testing) and F-68 (same-origin serving).

---

### F-85 — a session number was assigned by anticipation instead of by close-out
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

### F-86 — a reader for a PHI source emitted full phone numbers, because it was written against the source's shape rather than the destination's rules
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

### F-87 — a change was shipped to a test suite that could not be run offline, twice
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

### F-88 — a passing `md5sum -c` proved a kit was internally consistent, not that it was the intended kit
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

### F-89 — the cold-backup cadence lapsed for nine sessions, and three canonical documents were lost
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


---

## §7.1 (continued) — S182 · F-96 … F-99

### F-96 — the canonical set is PHI-bearing in a PUBLIC repository · RULED (D320)
**Found:** S182, by scanning all 48 canonical files after cloning the repo **anonymously** — which
itself re-proved F-90's open question: the repo is public, as a fact rather than a suspicion.
**What is exposed:** 7 unmasked patient mobile numbers, and — worse than S181 recorded — at least
two patient **names** and one clinic **patient ID** sitting directly beside them (the Callback-Tracker
audit; Archive v1.27/v1.28/v1.29, 14 hits in each). Six of the affected files were already in the
older `canonical-docs/` folder, so exposure is not new; the 16-Aug push multiplied it.
**Why it matters beyond the count:** a passing `md5sum -c` **conceals** it. The check proves
integrity and says nothing about whether the content belongs there at all — **F-88 one level up**.
**Ruling (D320):** the owner accepts the repo staying public, knowingly. Recorded as a decision, not
left as an open finding. **RULE (corollary, binding): no PHI-bearing artefact enters the repo** —
raw Marg exports, `finance.db`, patient CSVs and scans live on the PC and the VPS only (F-31/F-49).
Masking the canonical set is a separate and expensive decision — it would break every pin and the
Archive's prefix-proof, and must never be done as a quiet edit.

### F-97 — the Register's LIVE-CODE PINS are verified by nothing, and one was stale by two sessions · OPEN
**Found:** S182, before writing any code, by checking the obvious build path.
`portal.py` was pinned `da4177091ba9f188be6a0ff3eaf25bd8` "S176"; the repo copy matched that
**byte-for-byte**; the box was running **`34f038a7652024d49479569ed53bbfb9`** with two live finance
tiles present nowhere else. **The pin and the repo agreed with each other and both were two sessions
behind reality.** A full-file replacement built the obvious way would have deleted the medical unit's
**Daily Sale** and **Sanjeevni Medicos** tiles, and every gate would have passed — nothing asserted
their presence, and the matching hash would have actively reassured.
**The structural point:** Phase 0 verifies **documents**, beautifully. **Nothing verifies the live-code
pins in the Register at all.** The new git-clone Phase 0 makes that gap *easier* to miss, not harder,
because it feels total. A filename is not provenance (D188); **neither is a Register pin**.
**Mitigated per-kit, not structurally:** every portal kit now carries a **LIVE-FILE CURRENCY GATE** —
it refuses unless the live file is exactly the one the kit was built against, and says so having
touched nothing. **RULE: a full-file replacement states the md5 it was built on and refuses any other.**
**Owed:** something that verifies live-code pins as a class — the fix is not written.

### F-98 — the SSO broker assumed "doctor" when it could not identify the caller · CLOSED (S182_P2a)
**Found:** S182, while chasing why grant-only tiles vanished from the owner's portal.
`_authed()` accepts a valid SSO cookie **or** `_is_trusted()` (the legacy PIN-era device cookie kept
for the SSO transition), and `_is_doctor()` said, in its own docstring, *"a trusted device with no SSO
user is treated as the doctor."* So a browser holding that old cookie, **with no SSO session at all**,
was authenticated and treated as the doctor — reaching every `@doctor_required` surface: the Clinic
Gist, the Call Console, the per-staff coaching report. Patient-data surfaces. The likeliest browser in
that state is the clinic PC, shared by reception.
**This is F-84's pattern** — *anything that grants identity for convenience must be opt-in; the
production default must be closed* — minted on the finance app at S179, fixed there, and still sitting
in the broker that fronts everything else. **Defence in depth limited it:** `/portal/users` uses
`@user_admin_required`, which demands a real SSO user and 403s a trusted device; the finance app has
been fail-closed since F-84; downstream apps run their own verify-shims (D265).
**Fix:** identity is proven, never assumed — but keyed to `_sso_ready()`, **not** to the cookie. When
broker mode is available an unidentified caller is sent to sign in; when it is not available the legacy
path is untouched, so **D264's inert-on-failure invariant survives** and a config failure cannot lock
the owner out of his own front door. That branch is asserted as its own test.
**Second lesson, recorded:** this fault also produced the "my new tiles are missing" report. With no
identity, `USER_TILE_EXTRA` has no username to match and **every** grant-only tile vanishes — proven
by the *pre-existing* "Manage Users" tile vanishing alongside the new ones. **RULE: when a new thing
and an old thing fail together, the new thing is not the cause.**
**Gate:** 48 checks, including an identity matrix over all four (broker ready?, SSO user?) combinations
and **served-HTML** checks (D307c) rendering the real page for six named people, presence AND absence.
Proven to bite against the pre-fix file. Two of the gate's own assertions were wrong on first run and
the gate caught them — a bare `">Clinic<"` also matched the section header, and Darpan had been wrongly
expected to see a doctor-only tile.

### F-99 — a missing-day alarm anchored on the first filed day cannot see a unit that never files one · OPEN
**Found:** S182, from the clinic review screen showing every day 1–16 Aug as `pending`, never `missing`.
`refresh_missing_days()` anchors on `MIN(business_date)` for the unit and **returns 0 immediately when
the unit has no `day_entry` rows**; no exception is raised and the grid falls through to `pending`.
There is no `clinic.start_date` — the anchor is literally "the earliest day you ever filed."
**Consequence:** the alarm arms itself with the first filed day and is correct thereafter, but until
then **"this unit has not started" and "this unit has gone dark" are indistinguishable.** D313 commits
to missing days shouting; for a brand-new unit it cannot.
**Why it never bit before:** medical was seeded with 121 imported legacy days. **Clinic is the first
unit to start empty — and lab will hit exactly this when it launches.**
**Deliberately not fixed at S182:** a new anchor setting would mean another kit against a finance app
freshly green at 316/316, to cover a window that closes with the first filed day. **RULE: a detector
whose scope is derived from the data it monitors has a blind spot at zero, and that blind spot must be
written down when the detector is built, not discovered by a unit going dark.**


---

## §7.1 (continued) — S181 · F-90 … F-95 *(applied at the S185 close; owed since S181 — F-108)*

> **Provenance.** These six findings were minted at S181 and indexed in the **KB Register's** findings
> index, but were never applied to this register: §7 ended at F-89 and read *"Next free finding: F-90"*
> for four sessions (**F-108**). The bodies below are **derived from evidence, never from memory
> (D172)** — from `KB_Register_v5_5_S183.md` (md5 `3cad79e6361c6e1777f3bc9db983770d`) findings index
> "F-0 … F-95 (as at S181)", the v5.3 lineage row, and `HANDOFF_RUNBOOK` v115/v117. **Where the
> Register recorded a one-line finding, this entry states what the Register recorded plus what later
> sessions proved about it — it does not invent detail the record never held.** The Archive §S181
> block remains the authority for the surrounding session narrative.

### F-90 — the GitHub repository is PUBLIC · RULED (D320)
**Found:** S181, as an open question with visibility **UNKNOWN**; the recommendation was private + a
read-only deploy key. **Proven:** S182, by cloning the repo **anonymously** — which turned a suspicion
into a fact and answered F-9's long-open question in the same stroke. **Ruled:** S182, **D320** — the
repo stays public, knowingly, because the D317 chain and the git-clone Phase 0 both work unchanged
over an authenticated remote and the owner accepts the exposure. **Binding corollary: no PHI-bearing
artefact may enter the repo** — raw Marg exports, `finance.db`, patient CSVs and scans live on the PC
and the VPS only (F-31/F-49). Recorded as a decision rather than left as an open finding.

### F-91 — UPI is recorded as Cash at Docterz entry · OPEN (behavioural)
**Found:** S181, during the clinic/lab forensic analysis. ₹17,900 over six weeks was collected by UPI
and typed as Cash at the point of entry. **The reason it survived so long is the important part: it is
invisible to any ledger-internal check.** The books balance either way — cash in equals cash recorded —
so no invariant, no exception and no self-test can see it. **Only a comparison against the bank exposes
it**, and the typed daily tab is the reconciliation anchor.
**Its shape recurred:** at S182 two Marg days (11 and 14 Aug, ₹38,355) were 100% cash against 40–76%
on every other working day — F-91 appearing in the pharmacy rather than at reception. **Settled at
S183** as a Marg UPI-recording gap, bank-confirmed.
**Fix:** the reconciliation workbench designed at S184 — Marg ⋈ bank ⋈ entry on one screen, with
cash→UPI suggestions **graded like D315 and never auto-applied**, and a correction log through
`audit_log`. **RULE: a discrepancy that leaves the books internally consistent can only be found from
outside them.**

### F-92 — discount capture stopped on 18 Jun 2026 · OPEN
**Found:** S181. ₹1,33,720 of discounts were recorded up to 18 Jun 2026, and **zero after it.**
Concessions did not stop being given — they stopped being *valued*. Part of an **18–19 Jun regression
cluster** noted the same session. The money is not lost; the visibility is. Until it is restored, any
analysis of realised-versus-billed revenue after 18 Jun is quietly wrong in a direction nobody is told
about.

### F-93 — the concession parser swallows the Docterz footer · OPEN
**Found:** S181. The parser reads the report's footer as data, manufacturing **three fake "patients" a
day** in the staff-facing sheet. In money terms this is cosmetic. **In trust terms it is not:** a
staff-facing report that visibly contains nonsense teaches the people who read it that the report may
be ignored, which is expensive in a system whose entire premise is that the people at the counter
believe what it tells them.

### F-94 — an installer's environment assumptions are part of its specification · CLOSED by D317's rules
**Found:** S181, as the **C1a / C1b / C1c red trilogy** — three consecutive installer reds during the
clinic-module build. Each was caught by a gate with **nothing half-installed**, and each traced back to
an assumption about the target environment that the kit had never stated out loud. **Closed by rules,
not by a code fix:** the D317 kit chain requires a kit to declare what it needs and to refuse rather
than adapt. Kin of F-53 (which interpreter) and F-88 (which build).

### F-95 — a synthetic store proves logic, not life · CLOSED by rules
**Found:** S181, from the same build. A test database built to satisfy a suite proves that the *logic*
holds; it says nothing about whether the code survives contact with the real store's shape. **Three
rules were adopted:** smoke checks **print what they actually saw** rather than asserting silently;
invariants are **asserted as invariants**; and an offline store is **enriched with live-shaped data
before a first live gate** is attempted. Direct kin of **F-87** (a change shipped twice to a test suite
that could not be run) and the ancestor of **F-106** (a test that froze a data state).

---

## §7.1 (continued) — S183 · F-100 … F-104 *(applied at the S185 close; owed since S183)*

### F-100 — `push_kit.bat` reported success while git had silently dropped a kit file · CLOSED same session
**Found:** S183, at the VPS console, as a SUMS refusal — the only place it could surface.
The pin list was named `live_pins.tsv`, and `.gitignore` carries a blanket `*.tsv`: one of the
data-format guards that keep patient data out of a public repo (F-31/F-49, D320). **`git add <folder>`
says nothing about ignored files inside it**, so the kit was published incomplete while the publishing
step reported "pushed successfully."
**This is F-97's shape one layer up the toolchain:** the publishing record claimed a file that was not
there, exactly as a Register pin claimed bytes that were not there.
**Fixed two ways.** The file was renamed to `.txt` — **no exception was carved into `.gitignore`**,
because a blanket PHI rule with holes in it is how something eventually gets through. And
**`push_kit.bat` v4** now lists any excluded file **with the exact rule that excluded it** and REFUSES
to commit.
**RULE: a publishing step that cannot prove it published everything has not published anything.**

### F-101 — eight live files were recorded one directory too high · CLOSED, corrected
**Found:** S183, by the first run of `verify_live_pins.py`.
The call-hook/verdict family lives in `/root/wa/call-hook/` and `/root/wa/recordings-archive/`; the
Register said `/root/wa/`. Confirmed against **three independent sources** — the files themselves,
`call-hook.service`'s `WorkingDirectory`, and four live crontab lines. **Seven of the eight matched
their pinned md5 exactly: right bytes, wrong address.**
**The lesson is about severity, not bookkeeping.** A wrong path downgrades a **DRIFT** to a **MISSING**.
"Not there" reads as a filing error and gets waved through; "different from the record" reads as
danger. The eighth row proved the point — a genuine stale hash (**F-102**) was wearing a MISSING's
clothes and nearly stayed hidden behind it.
**RULE: a pin is an address AND a hash, and the address is verified with the same seriousness as the
hash.** *Recorded limitation of the checker itself: where a recorded path is wrong it reports MISSING,
and a MISSING masks a possible DRIFT until the path is chased down.*

### F-102 — a live-code pin was stale for the whole S140→S182 run · CLOSED, corrected
**Found:** S183, by the same first run.
`call_hook_capture.py` was pinned at its **S126** value while the live file had been replaced on
**12 Jul 2026 at 18:13**: 42,409 bytes / 894 lines on the box against 31,490 / 701 in the record. The
stale pin rode unchallenged through every Register bump for more than forty sessions.
**A second confirmed instance of F-97's class, and an instructive inversion of it.** At S182 the *repo*
agreed with the stale pin and the *box* was right; here the *repo* was right and only the *record* was
wrong. **The record is the weak point in both directions — which is precisely the argument for a check
that interrogates the machine rather than comparing two documents to each other.**
**No harm done, and measured rather than assumed:** the receiver was checked healthy in the same breath
— dual-key gate ON (`current=key_ea20dd previous=key_db8972`, ROTATION IN PROGRESS), 26 accepted /
0 refused — and the service's start time is later than the file's mtime, so the running worker holds
the current bytes. Corrected to `b8a1a293c54dfb6528e04fdf31f8d3e6`.

### F-103 — the finance system has no cash-deposit reconciliation against Yes Bank · OPEN (structural)
**Found:** S183, while explaining an impossible drawer balance of **−₹30,056**.
Sanjeevni cash is swept roughly weekly into a **Yes Bank** account, appearing as
`CASH DEP-SELF-SANJEEVNI MEDICOS`; **ICICI (…312505) receives card and UPI only.** `finance_upi`
reconciles the ICICI side. **Nothing reconciled the cash side at all** — so **16 real deposits totalling
₹16,45,600 between 9 Apr and 13 Aug went unrecorded**, the drawer chain broke, and the break was read
for months as missing money.
**Nothing was missing.** Reconciled: cash collected ₹17,98,033 − deposits ₹16,45,600 − expenses
₹84,442 = **+₹67,991** drawer growth.
**RULE: a break in a ledger is often an unrecorded real movement, not a loss. Before treating a
negative as missing money, ask what legitimate movement is unrecorded.** And: **the bank is the
arbiter, and here it cleared the human** — Darpan's declared UPI matched ICICI T+1.
**FIX still owed:** a Yes Bank cash-deposit reconciliation parallel to `finance_upi`, plus a named
"bank deposit (Yes Bank)" movement type so a sweep is *recorded*, never left as a carry-forward break.
*(The 16 deposits themselves were booked at S184 by `S184_C1a`; the mechanism that would prevent a
recurrence is not built.)*

### F-104 — the backfill fed identity-less legacy bills through attribution · OPEN (owner chose the fix)
**Found:** S183, in the exception counts after the 119-day Marg backfill.
April → mid-June bills carry a patient **name** but no clinic **ID**, so they route to review as
low-confidence under **D315**, leaving each day's attributed sum below its day total. Result:
**~2,062 review items and 118 `line_sum_vs_day_total` exceptions.**
**No money is affected** — attribution never moves `day_line` (**D313**, proven at scale by this very
backfill, which left the money byte-identical across 119 days). The cost is a review queue full of
legacy noise, which is how a real exception comes to be missed.
**Owner ruling: reclassify legacy no-ID bills to WALK-IN** — they attribute cleanly, the 118 exceptions
clear, and the queue empties of noise. To build and test offline, then apply.

---

## §7.1 (continued) — S184 · S185 · F-105 … F-108

### F-105 — the app blocked a data catch-up, and the block was correct · CLOSED (the system was right)
**Found:** S184, when Darpan's 14/15 Aug catch-up would not submit.
The Submit guard refused because the day's **opening carried the −₹30,056**, and the guard will not
accept a negative opening. **The S183 record had said in writing that this catch-up "needs nothing
above."** It did. **The record was wrong and the running guard was right** — the D313 invariant doing
exactly the job it was built for, at the exact moment it was inconvenient.
Resolved by fixing the *books* rather than the guard: after `S184_C1a` the two days were entered and
saved as drafts (the form requires three scans or a stated reason to Submit; the owner chose that
Darpan attaches scans and submits, with Manoj approving).
**RULE: the app enforcing correctness looks like an obstacle and is a feature. When a written record
and a running guard disagree, believe the guard** — the guard is executing, the record is remembering.

### F-106 — a self-test asserted a data state, and a legitimate correction made it fail · FIXED (S184_F1b)
**Found:** S184, when kit `S184_F1a` went RED at its install gate.
`finance_app.py --selftest` asserted the **pre-S184 store state**: cash negative, carry-forward breaks
open, marg unmapped. The session had just *corrected* all three, legitimately and deliberately — so the
session's own success registered as four test failures, and the gate correctly restored the previous
build. **The test was not wrong about the data; it was wrong about what a test is for.**
**Fixed in F1b** by making those four checks **state-adaptive**: 314/314 on the corrected store.
**Family:** F-88 (a checksum proves integrity, never currency) and F-97 (a pin proves agreement with a
record, not with reality). All three are the same error in different clothing — **a check that
validates a snapshot and presents the result as though it had validated a property.**
**RULE: separate invariant logic from store state. Invariants are asserted as invariants; state is
asserted state-adaptively or against a seeded fixture, never frozen.**
**Follow-up owed:** split the selftest into invariant-logic and seeded-fixture halves, so a data
correction can never again block a code deploy.

### F-107 — Phase 0 is blind to a document that was never listed · OPEN (structural); both docs filed + pinned at S185
**Found:** S185, at the session open, while reading the two Tier-0 documents the S184 close had produced.
`HANDOFF_RUNBOOK…v118` and `START_HERE_SESSION_185` had been written into **project knowledge only**.
They never reached the repo, never entered `MD5SUMS_ALL.txt`, and never became rows in
`CANONICAL_MANIFEST.md`.
**The consequence is exact: at the S185 open, the two Tier-0 documents Phase 0 is *required to read*
were the two documents Phase 0 *could not verify*.** They were read on trust. **Nothing reported a
problem, because nothing looks for a missing row.** Phase 0 walks the manifest and asks of each row
*"do these bytes still match?"* — it never walks the documents in use and asks *"is each of you
listed?"*
**This is F-97's documentary twin.** F-97: nothing verified the live-code pins. F-107: nothing detects
an unlisted document. **Both are absence-blindness — and absence, not corruption, is what this project
has actually lost documents to** (F-89: three canonical documents lost because a backup that was never
taken cannot fail loudly).
**Remediated at S185, honestly:** both files were written out from the project-knowledge copies, filed
into the repo, **hashed as delivered**, and pinned. Their md5s were **deliberately not invented** at the
S185 open — *"compute at freeze"* means a real hash still owed, not a placeholder to skip (D172/D188).
Those filed bytes are canonical from here.
**Structural fix still owed: the inverse Phase-0 check** — assert that every Tier-0 document about to
be read has a manifest row. Natural companion to `verify_live_pins.py`; same family of fix, one domain
over.

### F-108 — findings recorded in one register were never applied to this one · OPEN (index corrected here)
**Found:** S185, while building the owed append — by checking this register's own next-free number
against its last index row.
**§7's index ended at F-89 and read *"Next free finding: F-90."*** Meanwhile **F-90 … F-95 (S181) had
never been applied to this register at all**, and **F-96 … F-99 (S182) existed only as §7.1 full-text
blocks with no index rows**. The KB Register's findings index carried all ten, so **nothing was lost** —
but the *findings register*, the document whose entire purpose is to be the register of findings, was
four sessions behind and **announced that fact nowhere**.
**Compounding it: v2.18 bumped this file and left no CHANGELOG row** — reconstructed at this close.
**This is the F-45 family recurring.** F-45 was minted *by this register, at S149, for exactly this
failure*. v2.17 then reconstructed **six** versions that had each bumped the file and left no changelog
entry, and named the pattern explicitly. It happened again at the very next bump.
**The structural point, and it is F-107's:** a version bump that *adds* content is loud and gets
noticed. Content that was *never added* is silent, and silence is indistinguishable from success. Two
findings in one session, in two different documents, from the same blind spot.
**RULE: the next-free number and the last index row must agree, and that agreement is checked at every
append** — mechanically, not by intention.

---

## §7.1 (continued) — S186 · F-109 … F-114

**F-109 — the two invented characters.** At the S186 open the `finance_app.py` pin was completed from
the box: **`c66bec2b9ea8c11af9c4a4244541e96f`**, corroborated byte-for-byte by the `S184_F1b` kit
payload held in git, whose `KIT_ID.txt` and `SUMS.md5` carry the same value and whose installer
refuses to run unless the payload matches it. Two independent witnesses. The record carried
`c66bec2b76…` — **wrong in characters 9 and 10.** Tracing it: Runbook v118 and `START_HERE_SESSION_185`,
both written at the S184 close, record only **eight** characters. The ten-character form first appears
at the **S185 fold-in** and then in fourteen places across the canon, while that same session wrote in
its own mental models *"never invent a hash to make a table look complete."* Nothing broke, because a
partial pin is never machine-compared — which is the whole reason it survived.

**F-110 — the checker held the box to a draft.** `verify_live_pins.py` reported three DRIFT reds at
the S186 open. Its pin list declared `source: KB_Register_v5_5_S183.md · source_md5: ff509b01…`.
**Canonical v5.5 is `3cad79e6…`, and no file anywhere in the repo hashes to `ff509b01…`** — the list
had been generated mid-session from an intermediate draft that still carried pre-S183 values. So two
of the three reds were **false**: canonical v5.5 already recorded `marg_report.py` = `829f4344…` and
`marg_backfill.py` = `fa33ec8a…`, exactly what the box reported. The tool prints its own `source_md5`
on every run — the right instinct — but **nothing ever compared that md5 to the manifest**, so it
announced its own staleness for three sessions to no one. Fixed in kit `S186_V1a`:
`gen_live_pins.py` v1.1 refuses to build from a Register the manifest does not pin as CURRENT, and
`verify_live_pins.py` v1.1 refuses to *run* on a list carrying no verified-source attestation
(`yes` / `pending: <reason>` / absent → exit 2).

**A consequence worth recording:** the draft list had **no row under `/root/deploy/`**, and
`find_untracked` only scans directories containing a pinned file — so for three sessions **the checker
could not see its own directory.** Untracked rose 68 → 76 the moment it could.

**F-111 — the generator could not read the Register.** Regenerating exposed that `live_pins.txt` had
not been rebuilt since S183, so three later changes to the live-file table had never met the tool that
consumes it. All three were latent: (a) the two `*(applied marker; no file md5)*` migration rows added
at S185 **halt the generator outright** — v5.6 could not have produced a pin list at all; (b) the
`*(superseded)*` rollback row added at v5.6 would have been read as a **second live pin for the same
path**, holding `finance_app.py` to two hashes at once, one of which could only ever be DRIFT — a red
that can never go green is the halt that gets waved through (D316); (c) nothing refused two pins for
one path. Fixed in v1.1: superseded rows dropped **loudly**, duplicate paths halt the run, and a row
may declare *no file md5* **in words** (classifiable) while a **silent** omission still halts — D166,
where UNKNOWN is a correct entry provided it is written down as UNKNOWN.

**F-112 — the deposit that never happened.** The owner supplied the Yes Bank statement for
**1 Jul – 17 Aug**; its last transaction of any kind is **30 July**, and there are no August entries at
all. The 13 Aug ₹75,000 booked by `S184_C1a` as one of "16 verified" credits **did not occur**. Truth:
**15 deposits, ₹15,70,600**; the live books understated cash in hand by ₹75,000 until kit `S186_C1a`
removed it. **S183 wrote the warning itself** — *"13 Aug 75,000 is owner-confirmed; it falls after the
statement cutoff. Possible gap … check when booking"* — and S184 booked it with no check made. The
structural remedy is `finance_yesbank.py` (kit `S186_R1a`), which matches booked deposits against the
statement in both directions and, critically, reports a deposit booked where **no loaded statement
reaches** as `deposit_unevidenced` — **never as a pass**. Given the real statement and the uncorrected
store it flagged exactly the 13 Aug ₹75,000 and nothing else: 5 matched, 1 caught, zero false positives.

**F-113 — a correct statement that expired.** `marg_backfill.py` skips a day for which no `day_entry`
exists, prints `NOT FILED`, and closes with *"N of M day(s) reachable · K not filed (refused,
harmlessly)"*. At the 16 Aug run, 14 and 15 August had not yet been filed — Darpan's drafts came
afterwards — so the tool behaved correctly and reported honestly. **The skip stopped being harmless
the moment the days were filed, and nothing revisited it**: no flag, no exception, no marker; the only
trace was console output from a finished run. Remedied in kit `S186_I1a`: the portal upload path writes
a `MARG_DAY_NOT_FILED` `data_flag` for every date it skips. *(The CLI driver still lacks this — owed.)*
**This finding was diagnosed wrongly twice before it was settled** — first as a short export, then as a
driver abort. Both were plausible; both were disproved by reading the actual export with the live
parser (it contained 14 and 15 Aug, 23 and 10 bills) and by running the live adapter against it on a
throwaway store (23/23 and 10/10, `draft` no obstacle). D172 and D188 applied to a diagnosis rather
than to a hash.

**F-114 — the queue that could only grow.** `marg_report.py` warned *"10 of 33 bills carry no clinic ID
and will attribute to WALK-IN"*; `finance_ingest.resolve_patient`'s docstring said *"a line with no ID
lands on WALK-IN"*. On 14–15 August: **WALK-IN 0, review 10.** The gate three lines above
`resolve_patient` —
`if ln["confidence"] < min_conf or (not ln["clinic_id"] and not ln["patient_name"])` — diverted the
line before that function was ever reached, so a bill with **neither ID nor name** was parked in a
review queue with **nothing in it a human could resolve**: no name to look up, no ID to match. 2,062
rows by S186, ~10 more per clinic day. Fixed in kit `S186_I1a`: a line read cleanly but anonymous, from
a **structured** export, attributes to WALK-IN; **low-confidence** lines still go to review, and an
anonymous **OCR** line still goes to review because an unreadable scan looks exactly like an anonymous
one. Reversible without code: `ingest.anonymous_to_walkin = 0`. Diff: one line replaced, 17 added.
The legacy backlog was then cleared by kit `S186_W1a` (F-104): review 2,072 → **0**, flagged days
120 → **4**.

**The family these six belong to.** F-109, F-112 and F-114 are all *a record asserting something about
another component that nobody checked* — the same shape as F-97, F-107 and the S184 SQL narration
*"tracked in salary system"*. F-110 and F-111 are *a check that was never checked*. F-113 is the
subtler cousin: **a true statement with an expiry date and no way to notice it had passed.**


## §7.1 (continued) — S186 POST-CLOSE · F-115 … F-121 *(raised and fixed the same day, after the close was published)*

> **Why there is a post-close block at all.** The S186 close was built, verified, published — and then
> the first live-pin run against the published list came back **RED**. Chasing that one RED opened six
> more. Every one of them lives in the layer that is supposed to prove everything else: the publish
> step, the manifest, the checksum file, the pin list. **The findings below are not about the clinic's
> money or the clinic's code. They are about the machinery this project uses to know what is true.**

### F-115 — the method that publishes a kit cannot publish the record · FIXED

**Symptom.** The owner was told to paste `PUSH.bat` to publish the close-out. He did. It pushed, and
`HEAD` matched `origin/main` — a clean green. The last published commit was `deploy kit S186_W1a`, a
mid-session kit. The **entire close-out was still uncommitted**: three modified and seven untracked
files in `KB_canon_all/`, plus the whole `S186_V1b/` kit folder.

**Cause.** `PUSH.bat` derives its target from its own location — `for %%I in ("%~dp0.") do set
KIT_NAME=%%~nxI`, then `git add deploy_kits\%KIT_NAME%`. Correct for a kit. But `KB_canon_all` **is not
a kit**: it carries no `KIT_ID`-bearing `PUSH.bat` of its own, so no per-kit publisher can ever stage
it. The instruction "paste PUSH.bat" was unfulfillable as given.

**Why nothing caught it.** Every check passed honestly and none was asked the right question.
`PUSH.bat`'s F-100 gate proves *the kit it stages* is complete — it cannot notice a folder it was never
pointed at. `git status` said so plainly, but `PUSH.bat` does not read `git status` and the owner is
not asked to. And `HEAD == origin/main` is a true statement about the commit that exists, not about the
commit that should exist. Family: **F-107** (absence-blindness), aggravated because the absent thing is
the canonical record itself. Had it gone unnoticed, S187 would have opened Phase 0 against a repo whose
newest canon was S185 — and the manifest, itself unpublished, could not have reported its own absence.

**Fixed:** `PUBLISH_CLOSE.bat` at the repo root — stages the whole `deploy_kits` tree, prints the payload
before committing, and ends by comparing `rev-parse HEAD` to `rev-parse origin/main`, printing GREEN only
when they are the same hash.

> **RULE: the method that publishes a kit and the method that publishes the record are not the same
> method — and a publish is not verified until the record's own bytes are shown to exist on the remote.**

### F-116 — the linchpin pinned the current Register to a phantom · FIXED

`CANONICAL_MANIFEST.md`'s Register row read `d0da61a095435b1a3ef559c210788c37`, which is the real file.
Its **own Phase-0 filename footer** read `KB_Register_v5_11_S186.md` (`d5ec45a5…`). A full index of all
936 files in the repo — hashed as stored **and** with line endings normalised both ways — finds **no file
carrying `d5ec45a5`**. The token appears in exactly one place in the entire repository: that footer.

It is a leftover from one of the five v5.11 intermediate states, or it was never real. Both are the same
fault: **a hash written from something other than a file.** Direct descendant of **F-109**, where two
characters were added to a partial pin "to make it look complete" — and this time inside the document
every other document is verified against. Phase 0 hash-compares every row; at the S187 open this token
halts the session on the linchpin.

> **RULE: a hash is transcribed from a file or it is not written. A document's own footer is a claim
> about itself and gets checked like any other claim — the body being right does not acquit the footer.**

### F-117 — the pin list attests to a manifest that does not exist · list fixed, TOOL FIX OWED

`S186_V1b/live_pins.txt` header: `manifest_md5: 04eff42ce5f642e9ebadbcdfc4f7f5a2`. The published manifest
is `d1f97e1a…`. No manifest anywhere hashes to `04eff42c`. The list was generated mid-close against an
intermediate manifest that was then re-pinned twice — **the attestation was true when written and expired
without anyone being able to notice.**

The deeper fault is in the tool. `verify_live_pins.py` v1.1 was built at this same session to close F-110,
and it reads only the *word*: `register_pin_verified: yes|pending|absent`. It then **prints** the manifest
name and md5 as though verified — `source : VERIFIED against the manifest CANONICAL_MANIFEST.md (md5
04eff42c…)` — without ever comparing that md5 to a file. The live run shown to the owner printed exactly
that line while the md5 in it was fiction. **F-110 was "a checker that could be stale never checked its
own source"; F-117 is that same checker, one level up, trusting a word where it could have compared bytes.**

**Fixed for now** by regenerating the list against the corrected manifest (`S186_V1c`). **Owed at S187:**
`verify_live_pins.py` must hash the manifest it names and refuse when the md5 does not match — the check
is three lines and the failure it prevents is the one that made this finding.

> **RULE: an attestation is a promise; a hash is a proof. A tool that prints a hash it never compared
> is manufacturing confidence.**

### F-118 — a duplicate-pin conflict resolved toward the superseded build · FIXED (the RED)

The first live-pin run against the published list: **RED, 1 drift.**

```
DRIFT  /root/finance/finance_ui/finance_workbench.html
       record says : 45cb85b353ba8675114ca23eaa6afa90
       box is  now : 18c71e63e5f1790c07d7fa3df53cd24e
```

`finance_workbench.html` shipped **twice** at S186 — first in `S186_R2a` (`45cb85b3…`), then a newer build
inside `S186_I1a` (`18c71e63…`). The box carries the I1a build, correctly: I1a installed after R2a and
passed 351/351. The Register pinned the **R2a** value. `18c71e63` appeared **nowhere** in the canon.

**Cause.** At the close the duplicate-path guard — built the same morning as part of the F-111 fix — fired
because the Register pinned one path twice. The conflict was resolved by deleting a row, and **the row
deleted was the current one.** The guard did its job: it proved two pins disagreed. It cannot say which is
true. That question was then settled **from the documents instead of from the box**, which is the precise
inverse of **D321(d), "the box wins."**

**This is the first RED in the project's history caused by the record rather than by the box** — and it is
therefore the first proof that the pin checker earns its keep in the direction nobody designed it for.
Blast radius nil: no live file was ever wrong, and a full-file replacement built on the stale pin would
have overwritten the newer workbench with the older one — which is exactly **F-97**, the fault the whole
pin system exists to prevent. **The system caught the fault the system was built to catch, in its own
records.**

> **RULE: a guard that detects a conflict must never be allowed to resolve it. Two pins for one path is a
> question, and the box answers it — not the document, and not the person tidying the document.**

### F-119 — Phase 0's only command failed, and nothing said so · FIXED

`START_HERE_SESSION_187` gives the next session one mechanical command: clone the repo and run
`md5sum -c MD5SUMS_ALL.txt`. Run today, it returns **70 OK, one "No such file or directory"** for
`KB_Register_v5_10_S186.md`, and a non-zero exit. v5.10 was an intermediate bump; when v5.11 replaced it
the row was never removed. **The door to Session 187 was locked and the lock was invisible** — nobody runs
Phase 0 at the end of the session that wrote it.

Note the shape: the checksum file was *internally consistent* with itself and *inconsistent with the
folder*. That is **F-88** stated in reverse, and it is why the inverse check now runs too: every file on
disk is either listed or explicitly excluded with a reason.

> **RULE: a close-out is not finished until the next session's opening command has actually been run and
> seen to exit clean. Writing the instruction is not testing the instruction.**

### F-120 — three checksum files for one folder, two of them stale · FIXED

`KB_canon_all` shipped `MD5SUMS_ALL.txt` (71 rows, authoritative and named by `README_VERIFY.md`),
`SUMS.md5` (52 rows, **4 mismatches**) and `MD5SUMS.txt` (10 rows, **1 mismatch and a malformed line**).
Nothing reads the latter two; they are residue from earlier kit shapes. But a folder that ships three
answers to "what are the correct bytes here" has no answer — and two of the three would convict a correct
file. **D202's one-authored-source rule, broken inside the folder that rule exists to protect.**

**Fixed:** `MD5SUMS_ALL.txt` is the single authority; the other two are in `deploy_kits/_attic_S186/`,
moved and **not deleted**, so the bytes and their history survive.

> **RULE: one folder, one checksum authority. A second one is not redundancy — it is a coin toss.**

### F-121 — a gate widened in scope started crying wolf · FIXED

`PUBLISH_CLOSE.bat` v1 kept F-100's gate ("any file `.gitignore` excluded from what I staged is
suspicious") while widening `git add` from one kit folder to the whole `deploy_kits` tree. Pointed at
eleven sessions of history it immediately refused the commit — over two `__pycache__/*.pyc` files in S182
kits and a stray `live_pins.tsv` in S183. All three are ignored **on purpose**; none was in the payload.

It refused for the wrong reason, and nothing was committed or pushed — the failure was safe. But a gate
that fires on old junk is a gate the operator learns to click past, which is **D316** exactly.

**v2 narrowed the scan to folders with staged changes — and failed identically on the next run**, because
the retired junk had been moved into `_attic_S186/`, which *was* a staged folder. **Both versions were
asking a proximity question — "is anything ignored *near* what I staged?" — and proximity is not the
fault.** The fault F-100 describes is precise and content-based:

> **did `.gitignore` drop a file that the payload's own checksum list names?**

`SUMS.md5` (kits) and `MD5SUMS_ALL.txt` (the canon set) **are** that list. **v3** verifies every name in
that list against `git ls-files` — exact, and structurally blind to junk that was never payload. Ignored
files are still printed, as INFO, and do not block.

v3's own rehearsal then caught a third form of the same error before it could waste a run: the *retired*
`SUMS.md5` moved into the attic was read as though it described the attic. Two fixes, both principled —
a retired list is renamed so it cannot pass for a live one (**the F-120 lesson applied to itself**), and a
folder is treated as a payload **only if it carries `KIT_ID.txt`**, which is exactly what makes a folder
publishable. Rehearsed three ways: the real payload PASSES, an un-tracked `live_pins.txt` is REFUSED, and
restoring it PASSES again.

> **RULE: scope a check to its payload — and define "payload" by what the payload declares about itself,
> never by what happens to sit next to it. A check that fires on things outside the payload does not add
> safety; it spends the operator's willingness to stop.**

> **RULE: rehearse a gate against a real refusal before shipping it. Three versions of this one were
> written; the first two were shipped unrehearsed and both failed on the owner's screen. The third was
> rehearsed and its two remaining defects were found in the rehearsal, not by him.**

**The family these seven belong to.** F-115, F-116, F-119 and F-120 are all *a record that describes a
world it was never compared against*. F-117 is *a check that prints a proof it did not perform*. F-118 is
*a conflict resolved by preference instead of by measurement*. F-121 is the mirror of all of them — a check
so eager it stops being read. Six of the seven were found **only because one RED was taken seriously**;
the seventh was found while fixing the first. **The RED was not the problem. The RED was the only thing
working.**

---

## §7.1 (continued) — S187 · F-122 … F-126 *(appended at the S187 close, the session they were raised)*

> Session 187 shipped **eight kits in one session** — the F-117 structural fix, B5 (the pushed Marg
> export), Daily Flow v2 stage D1, the portal tile chain, and the owner's Sanjeevni Hub with the
> Clinic Design Language — and raised five findings on the way. Three are about the **publishing and
> attestation chain** (F-122, F-123, F-124: the record-keeping machinery asserting things it never
> verified), one is the **test-discipline family firing a fourth time** (F-125), and one is a new
> **installer-shipping rule** (F-126). None is a surveillance code.

### F-122 — the generator minted a phantom manifest hash at every generation, and the checker printed it as a pass · CLOSED STRUCTURALLY (kit `S187_V1a`)

**The session's first act was Runbook v121 item 0 — and the fault fired live while being fixed.**
The `S186_V1c` pin list attests `manifest_md5: 78881ddd0b73ce51ffdbaa7e35bc95e4`. An md5 index of the
full 157-commit history — all 24 committed manifest states, both line-ending normalisations — matches
it **nowhere**. V1b's `04eff42c…` is the same, and F-116's `d5ec45a5…` before that: **three phantom
manifest hashes in two sessions, all minted by the same mechanism.**

The mechanism is structural, not a slip. The manifest's own self-row reads *"recomputed last, each
EOS"* — so at the moment `gen_live_pins.py --manifest` hashes the file, it is hashing a state that
the close-out will edit again before publishing. **A true hash of a state that no longer exists is
indistinguishable from an invented one.** The Runbook's "~3-line fix" (hash the named manifest,
compare) was therefore **unbuildable as written**: there is no stable whole-file value to compare TO.

The real fix required noticing that the box **does** hold the canon: `/root/deploy/repo` is the D317
chain's clone, git-pulled at every install. **v1.2 of both tools:**
- `gen_live_pins.py` **never writes the manifest's whole-file md5 again.** It writes
  `manifest_current_register_pin` — the md5 the manifest's CURRENT `KB_Register` row carries, which
  is **stable** (it changes only when the Register version changes) and **IS the claim** being made.
- `verify_live_pins.py` **proves the claim on this machine**: it finds the file in
  `repo/deploy_kits/KB_canon_all/` that hashes to the pin list's `source_md5` (**by hash, not
  filename — D188**), parses the `CANONICAL_MANIFEST.md` beside it, extracts its CURRENT Register
  pin, and compares. **The word VERIFIED is printed only after both comparisons pass**; every other
  outcome states its reason and caps the verdict at AMBER. A stale repo clone fails the hash-hunt
  naturally, so staleness reads AMBER with a pull hint — never false-GREEN.

Selftests: checker 43/43 (VERIFIED only on proof · GREEN only on proof · stale-repo → pull hint · a
manifest with two CURRENT Register rows refuses rather than guesses) · generator 22/22. Proven
against the real repo clone before shipping; the F-110 draft hash `ff509b01…` correctly refuses.

**Family:** F-109 (a hash written beyond its evidence) · F-110 (a phantom source hash) · F-116 (a
phantom self-reference) · F-117 (the checker printed an untested claim). **RULE: never attest to the
hash of a file whose rules say it will change after you hash it; attest to the stable value inside it
that constitutes the claim — and a checker may not print a claim it did not test.**

### F-123 — two manifests in one repo, the stale one still calling itself canonical · FIXED at this close

Found en route to F-122, by the hash-hunt that indexes the repo. The repo carried **two divergent
`CANONICAL_MANIFEST.md` files**: the real linchpin in `deploy_kits/KB_canon_all/` (S186 post-close,
checksum-covered), and `canonical-docs/CANONICAL_MANIFEST.md` — **nine sessions stale, "STATUS:
canonical — current at S177" in its own header**, sitting beside sixteen superseded Fault-Register
and Runbook versions, covered by **no** checksum file. Any tool or session pointed at
`canonical-docs/` would attest against S177 canon and report success.

**F-120 recurring one level up: rival checksum files became rival manifests.** Retired at the S187
close: the `canonical-docs/` folder moved to `deploy_kits/_attic_S187/canonical-docs/` (**moved, not
deleted**), its manifest **renamed** (`CANONICAL_MANIFEST.md.RETIRED_S177_stale`) so it can never
again pass for a live one — the F-120 lesson applied to itself — and a one-line `README_RETIRED.md`
pointer left at the old location. **RULE: exactly ONE file in the repo may be named
`CANONICAL_MANIFEST.md`; a superseded copy of a self-describing document must be made to say so,
because its own STATUS line outranks its folder name in every reader's eyes.**

### F-124 — the publisher swallowed a fatal and printed success · FIXED the same hour (`PUSH.bat` v2; `PUBLISH_ALL.bat` default)

The `S187_V1a` publish failed exactly this way, live: a stale `.git/HEAD.lock` (the `.git` folder
carries a graveyard of them from S185/S186 crashes) blocked `git commit` with a **fatal error**;
`PUSH.bat` v1's `|| echo (nothing new to commit - continuing)` read the fatal as an empty commit,
pushed nothing, and printed `---- S187_V1a pushed`. Origin HEAD proved it: unchanged.

**The fourth publishing fault in three sessions** — F-100 (success while git dropped a file), F-115
(the publisher could not carry a close-out), F-121 (the widened gate cried wolf) — **all the same
shape: the tool asserted an outcome it never verified.** Fixed in v2: refuse up front on
`HEAD.lock`; run `git diff --cached --quiet` BEFORE committing so "nothing to commit" is decided
ahead of time and a commit failure can only be real; after pushing, **verify `git rev-parse HEAD`
equals `git ls-remote origin HEAD` and refuse to print success otherwise** — the projection is the
check, applied to publishing. v2 proved itself in the field the same hour: one honest refusal on the
lock, one verified publish. At the session's end the same gates were folded into
**`PUBLISH_ALL.bat`** — one whole-repo publisher (add-everything + F-100 gitignore gate + lock
refusal + real-failure commit + origin-HEAD verification), adopted as **the default publish method**
(D328) and proven on its first field run, which published kit `S187_H1c` and the sender's desktop
dressing in one verified push. **RULE: `|| echo` is how a fatal becomes a footnote; a publisher may
print "pushed" only after comparing the remote to the local head.**

### F-125 — a state-asserting test, broken by the first real datum · FIXED (kit `S187_P1b`)

The `S187_P1a` install went **RED on the live store — 388/389 — and the one failure was OURS.** The
M1a-era check *"staging holds exactly one pending row"* counted ALL pending rows in
`marg_push_staging`; that very morning **reception's first genuine push from the medical PC** had
landed a real pending row (test stub + real push = 2). A test that was true until the world produced
real data — **F-106's exact pattern inside a test, and the fourth time this family has fired**
(F-84's "test asserting an environment accident" · F-87 · F-106). The D317 gate did precisely what
it exists for: restored finance byte-perfect, never touched the portal, **no incident** — the RED
was the system working.

Fix: the check is scoped to the test's **own bytes** (`file_md5 = md5(stub)`) — behaviour, not store
population. Then **re-rehearsed against the exact failing condition**: a copy of the store seeded
with a real pending push passes the full suite with the differential clean. **RULE: a test asserts
behaviour, never store population — and a fixed test is re-run against the state that broke it, not
against the state where it always passed.**

### F-126 — an installer whose goodbye died after all the real work had succeeded · FIXED (standing rule)

`install_h1a.sh` completed every real step — gates green, page placed, pins updated, 400/400 — and
then aborted on a **syntax error in its own tail**: a sed-injected echo had broken shell quoting in
the closing message. Harmless in effect, poisonous in principle: **an installer that dies after
acting is indistinguishable, at the console, from one that died before** — the operator is left to
forensically determine what applied. Cause: string-surgery on a shipped installer, verified only
along the rehearsed path (which exercised the gates, not the goodbye).

**Standing rule adopted: every installer is syntax-checked WHOLE — `bash -n install_*.sh` — before
it ships.** A rehearsal exercises one path; `bash -n` reads them all. Applied to `install_h1b.sh`
and `install_h1c.sh` the same session (both carry the check in their headers), and owed to every
future kit. Kin: F-63 (the wired route never exercised) — the same lesson at the shell layer.

---

**The family these five belong to.** F-122 and F-124 are *a tool asserting what it never verified* —
the F-88/F-97 lineage reaching the attestation and publishing layers. F-123 is *a stale record
wearing a current label* (F-45/F-108/F-120). F-125 is *a test asserting the world instead of the
behaviour* (F-84/F-87/F-106), caught by a gate built four findings earlier. F-126 is new: *the
untested path was the exit*. Four of the five were fixed the same session; the fifth (F-122) was
fixed structurally by removing the possibility of the claim, which is the only durable kind of fix
this family has ever accepted.

---

## §7.1 (continued) — S188 · F-127 … F-129 *(appended at the session they were raised)*

> Session 188 built **Daily Flow v2 stage D2** — Darpan's mirror: save, see the bank and Marg
> check, then file. Two kits shipped and both went green to a projection written down first
> (`S188_D2a` 400/400 → 453/453; `S188_D2b` 453/453 → 464/464). Three findings came out of it, and
> the shape of the session is that **two of the three were found by building the fix for the
> first.** None is a surveillance code.

### F-127 — a role gate on the surface is not a role gate on the data · FIXED + INSTALLED (kit `S188_D2a`)

**What happened.** Stage D2 required a maker-scoped view of a day, so the existing surfaces were
read to see what the maker already had. `/finance/api/tile` — the endpoint Darpan's entry page has
called on **every page load since S179** — carried **no `require(...)` at all**.

It is not an open door. `_gate` refuses anyone without a role on the medical unit, and its own
docstring says it "protects future routes automatically". It does — at **unit** granularity. What
it does not do is distinguish maker from checker *within* a unit. So a route that needed `checker`
and simply forgot to say so was accepted for the maker, silently, and looked protected the whole
time.

**What his browser actually received on every load**, to render one deposit banner:
`cash_in_hand` · `cash_with` (the custodian's **name**) · `month_to_date` · `last_revenue` ·
`last_filed` · `deposit_threshold` · `deposit_excess` · `last_bank_deposit` ·
`days_since_bank_deposit` · `bank_trip_due` · `noncash_month_to_date` · `awaiting_approval` ·
`last_month_close` · every shout count. **`/finance/api/exceptions` was the same shape** — ungated,
returning every open exception in the unit, while the page used only the missing-day rows.

**The family.** **F-84** (S179) minted "the offline-testing shortcut was the vulnerability" and
closed three ungated reads. These two were not among them — because the unit gate made them look
covered. This is that fault one layer in: not *no gate*, but *the wrong gate, mistaken for the
right one*.

**A stale claim nearly argued the fix away.** `api_tile`'s docstring read *"Feeds the portal
tile."* It has not since **S187**: the portal reads `my-day-summary` and `tile-summary`. Checked
against the live `portal.py` bytes rather than believed — the D188 discipline applied to a comment.
Had it been trusted, gating the route would have looked like breaking the portal.

**Fixed** (`S188_D2a`, live, smoke 453/453): `tile` → `require("checker")`, payload otherwise
untouched · `exceptions` → maker+checker, and **a maker receives only `missing_day`** · `day/<date>`
→ maker+checker, payload unchanged because it was already correctly scoped · the deposit banner and
its fetch removed from the page, proven by an **absence check on the served bytes** (F-79), which is
the half a presence check can never catch.

> **RULE: a route states its own role.** A gate that protects the unit boundary does not protect the
> role boundary inside it. The absence of a `require(...)` on a route is a defect, not a default.

### F-128 — the rehearsal harness granted the privilege the tests existed to deny · FIXED (`dev/dev_seed_smoke_db.py`)

**What happened.** F-127's fix is a role refusal, so it needed a test that a maker is refused. It
would not go green. The cause was not the fix: `dev_seed_smoke_db.py` — the S180 tool built as
F-87's own remedy, so the suite could be rehearsed offline at all — seeded
`unit_role(medical, selftest, checker)`.

The live box has **no unit_role row for the smoke user**, so on the box the header role alone
decides. Offline, the smoke user silently carried checker rights on every run. Every
*"a maker cannot cutover"*, *"maker cannot post statements"*, *"a maker cannot allocate deposits"*
assertion — **eight of them** — had been passing without testing anything, for as long as the
harness has existed.

**Correcting one line moved the offline baseline 375 → 398**, and that number is the measure of how
much signal the fixture had been absorbing.

**The shape of it.** The F-106 family is *a test asserting the world instead of the behaviour*
(F-84 → F-87 → F-106 → F-125, four firings). This is that family **inside the harness built to
rehearse for it** — the fixture handing out the very privilege the assertions existed to deny. The
harness is not exempt from the discipline it exists to serve.

**Consequence for this session, stated plainly:** the three new F-127 refusal tests are written to
run as `smoke_no_seat`, a seat with no role rows at all, so they refuse from a genuinely
role-less caller rather than from a header the fixture can override.

> **RULE: a test fixture must not grant the privilege the test exists to refuse.** A refusal is
> asserted from a seat that genuinely lacks the role, never from one the fixture has quietly seated.

### F-129 — a marker recorded that something was shown, but not to whom · FIXED + INSTALLED (kit `S188_D2b`)

**What happened.** D2a's `edited_after_reveal` badge (D326: the stamp, not the lock) rests on a
`day_mirror_reveal` row recording that the bank/Marg check had been shown, plus a fingerprint of the
money at that moment. The row was keyed on the **day**, whoever opened it. So:

1. Darpan files a day.
2. The **checker** opens it to look — the badge arms.
3. Darpan corrects a figure.
4. **Darpan** is stamped *"changed after the check"* — for a check he was never shown.

**Why it matters more than it looks.** The flag would have been *literally true*: the figures did
move after the day was cross-checked. It would simply have been **about the wrong person** — and
the badge exists precisely to describe the maker's sequence, which is the one thing stage D2 is
built to protect. A record that is true and misattributed is harder to catch than one that is
false, because nothing about it reads as wrong.

**Near relative of F-118** — *a record asserting something about another component is a claim, not a
fact.* Here the reveal row asserted something about the maker's sequence that it had never observed.

**Caught before any live use**, while writing the owner's first-look instructions: the safe advice
would have been "open an approved day, not a draft", and the fact that the advice needed a caveat
was the signal.

**Fixed** (`S188_D2b`, live, smoke 464/464): the reveal arms only when the caller holds `maker` and
not `checker`; the endpoint answers `looking_as_maker` and `armed_by_this_look`; the page renders a
**read-only** row when the look is a checker's, so the person reading knows which of the two things
just happened; the flag's own text now names whose sequence it describes. **One assumption written
into the code rather than left implicit:** a caller holding both roles counts as the checker and
does not arm the badge — on medical no such person exists (the checker is the doctor alone, S179),
and the comment names the line to revisit if that ever changes.

> **RULE: a marker that records "this was shown" must record WHO it was shown to, or it will speak
> about somebody else.**

### F-130 — the design of a page is invisible to the tests that guard it · OPEN, fix specified

**What happened.** The owner sent a saved copy of `/finance/approvals` to look at. It was plainly
the pre-H1c design — old blue-grey palette, no logo, no sticky header, no stat tiles. The record
said H1c (`02825505…`) was live. **Nothing we own could tell which was true.**

The suite had just run **464 checks green**. Not one of them could distinguish the two, and the
reason is structural rather than accidental: **H1b and H1c shipped as page-only kits with every
element id and API path byte-preserved.** That preservation is exactly what made them safe to ship
— and exactly what makes them undetectable. A page could revert to a nine-session-old design and
every gate would stay green.

Settled the only way it could be: `md5sum` on the box. It matched; the saved copy was simply taken
before H1c installed. **The answer was reassuring and the method was not** — a hash typed at a
terminal is not a gate.

**Remedy, already half-applied by accident.** The S188 entry-page suite asserts
`--surface-page:#f3f2ee`, `id="toTop"`, `class="kick"` and the folded-help block — a **design
fingerprint**, deliberately something the kit did *not* preserve. The same three lines on
`approvals`, `workbench` and `review` close this. Queued at the head of the S189 backlog.

> **RULE: when a kit deliberately preserves every id, the test must assert something the kit did
> NOT preserve.** Otherwise the change and its absence are indistinguishable, and a green suite is
> reporting on a question it was never asked.

### F-131 — `git status` is not read-only, and four sessions of evidence sat unread · FIXED in practice

**What happened.** Checking whether a kit had been published, `git status` was run against the
owner's repo through the desktop bridge. `git status` **refreshes the index**, which means creating
and then deleting `.git/index.lock`. The bridge forbids deletes. The lock survived, and the owner's
next `PUBLISH_ALL.bat` failed on it.

Git said so at the time:

```
warning: unable to unlink '.../.git/index.lock': Operation not permitted
```

That line was in the tool output and was read past. **F-119's rule — a warning is a failure —
applied to a person instead of to a script.**

**What clearing it revealed.** `.git/` contained **fourteen** renamed locks, dated across four
sessions:

```
S185: stale_1786905261 · stale_S185_safe_to_delete
S186: stale_S186 · s6 · s7 · sD · z3 · z4 · cleared_final
S187: stale_S187close · stale2_S187close · stale4
S188: stale_S188 · stale_S188b
```

The names tell the whole story — `z3`, `z4`, `cleared_final`. **Every session hit this, worked
around it by renaming the lock, and moved on. Not one recorded it.** So every session rediscovered
it from scratch, and this one paid for it with a failed publish. **The F-45 family in its purest
form**: a known problem with no entry, where the workaround was always cheaper than the record
until the moment it wasn't.

**One thing behaved correctly and deserves saying:** `PUBLISH_ALL.bat` hit the lock, printed
`git add FAILED`, and committed nothing. That is **F-124's** fix earning its keep — the older
`PUSH.bat` would have printed "pushed" over the top of a swallowed fatal.

**Fixed in practice:** `git --no-optional-locks status` returns the same state and **provably
leaves nothing behind** (verified immediately after clearing). No bare `git` command is run against
the mount again. **Owed:** the owner deletes the 14 files — the bridge cannot, which is the same
restriction that caused this in the first place.

> **RULE: a command that looks read-only is not read-only until its side effects have been
> checked.** And **a workaround repeated without a record is not a solved fault — it is a fault
> scheduled to be rediscovered.**

**The through-line of the five.** F-127 is *a boundary mistaken for a different boundary*. F-128 is
*the F-106 family inside the harness built to catch the F-106 family*. F-129 is *a true record
pointed at the wrong subject* (F-118). F-130 is *a suite reporting on a question it was never
asked*. F-131 is *a warning read past, fourteen times, by four sessions*. All five are one habit —
**a check that looks like it covers something it does not** — and in every case what exposed it was
building the next thing on top and finding the ground would not hold.

---

---

## §7.1 (continued) — S188 POST-CLOSE · F-132 … F-133 *(raised after the close was published, and fixed the same day)*

> The S188 close was written, verified and published. The owner then logged into Darpan's own
> account from an incognito window on his phone, looked at the page, and asked one question:
> *"it is showing total amount also."* **That one look reopened the session and produced the two
> findings below** — the first of which was mine, recorded as fact hours earlier without a test.

### F-132 — "already correctly scoped" was a claim, not a test result · FIXED + INSTALLED (kit `S188_D2c`)

**What happened.** Closing **F-127**, three routes were gated. For `/finance/api/day/<date>` the kit,
the Register and the message to the owner all said: *"payload unchanged, because it was already
correctly scoped."* **Nobody looked at the payload.**

`opening_p` is computed by `v_cash_ledger`:

```sql
ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
```

**Unbounded preceding.** A running total of every day since the books began. The maker's page
labelled it *"Opening cash · carried from the last filed day"* and rendered it at **24px bold**,
with "Closing cash" beneath at **30px**. It was the whole unit cash position, twice, in the largest
type on the screen.

**The worse half is that it was not true of him.** Most of that balance is parked with Dr Bhawna
(D323) and ~₹87,205 of it is a pre-April adjustment (S186). A label reading *"carried from the last
filed day"* invited the maker to believe his drawer held two lakh rupees. **That half predates
F-127 entirely — it has been on the page since S179.**

**Three doors, not one.** The GET, the **save response** (`api_save_day` returns the same
`day_state`), and the D2 mirror built earlier the same day. Fixing the first surfaced the second;
fixing the second surfaced the third.

**Fixed** (`S188_D2c`, live, 478/478): withheld from a maker on all three; the checker's payloads
byte-unchanged; the page's opening and closing display removed along with the now-dead CSS.
**Nothing is weakened.** The carry-forward is safe because it is **computed on the server and never
accepted from a client** — that is what made the 36 legacy breaks impossible, not the display. The
client-side "would this go negative" courtesy went with it; the server has always refused with
`negative_cash` and still does.

> **RULE: "already correctly scoped" is a test result or it is nothing.** A payload named for one
> day may still carry a window over all of them — and the field label is not evidence about the
> query behind it.

### F-133 — the entry has existed since S179 and has never once been used · OPEN

**What happened.** The owner asked that Darpan be shown money parked with him and with Dr Bhawna.
Before building it, the box was surveyed. **The survey was the finding:**

```
cash_movement, all time, medical:
   bank   out   n=15   Rs 15,70,600.00
   (no other rows at all — not one to either doctor)
last bank deposit : 2026-07-30, Rs 85,000   → 19 days ago (threshold 7)
cash_custody_event: 0 rows
v_cash_custody_balance: empty
```

**Had it been built unsurveyed, the page would have displayed `Dr Manoj ₹0 · Dr Bhawna ₹0`** —
confidently, in the clinic's own software, while roughly two lakh rupees sat with one of them. A
worse falsehood than the one the same kit was removing.

**And it explains the ₹2,05,198.** S184 and S186 recorded *"cash parked with Dr Bhawna ahead of a
bank trip"* as **exception text** and as **`negative_cash` labels** — never as **cash movements**.
So the ledger has counted parked money as in-hand ever since. The money physically left the drawer;
in the books it never did.

**The capability was never missing.** *"Cash out / cash back — Bank, Dr Manoj, Dr Bhawna, both
directions"* has been on that page since S179. Fifteen bank deposits were entered. Not one handover
was. **The gap is practice, not code** — which is why no kit closes this finding.

**Mitigated** in `S188_D2c`: the zero is rendered as an **instruction, never as a fact** —
*"Nothing has been recorded — not once. If cash has gone to Dr Manoj or Dr Bhawna, enter it under
Cash out / cash back below. Until it is entered, the books count that money as still sitting in the
drawer."* Parked totals are scoped to the current financial year on the owner's instruction; the
bank clock deliberately is not.

**STILL OPEN, and it is about the owner's books rather than the maker's screen:** the ledger's
"cash in hand" is overstated by whatever is genuinely with the doctors, and **no record exists to
net it down**. Closing it needs the handovers entered retrospectively, or a counted reconciliation
of the kind S186 performed for the drawer.

> **RULE: survey the box before building a display of its data.** A zero rendered from a table
> nobody has written to is indistinguishable, on screen, from a zero that is true.

### F-134 — a close-out step performed once and never written down · FIXED (routine gains A8)

**What happened.** With the post-close canon published, the owner ran the proper end-of-session
check — `python3 /root/deploy/verify_live_pins.py` — and it went **RED on two files the box had
exactly right**: `finance_app.py` and `finance_ui/finance_entry.html`, the two files S188 changed.

The drift was in the **list**, not the box. `/root/deploy/live_pins.txt` was still the one generated
at the **S187 close**, from **Register v5.22** — three Register versions stale.

**Why.** `live_pins.txt` is generated **from the KB Register**. A Register bump makes it stale by
definition. S187 knew this and regenerated it, and its manifest block says so:
*"the pin list is regenerated from Register v5.22 against THIS manifest … and ships beside the canon."*
**But that is narrative, not procedure.** `END_OF_SESSION_PROMPT_v4` §A runs A0 → A7 and stops at
*"CANONICAL_MANIFEST.md — the linchpin, ALWAYS updated last."* **There is no A8.** So the S188 close
rebuilt the manifest, `MD5SUMS_ALL.txt` and `KIT_ID.txt` — and never touched the pin list.

**The tool was flawless, and that is worth recording separately.** It did not quietly pass on a
stale list. It printed `source : ATTESTED BY THE GENERATOR -- NOT PROVED HERE`, raised
`MANIFEST_MISMATCH`, and showed the CURRENT pin it expected (`9b713355…`) beside the one the list
actually carried (`116a0bdb…`). That is **F-122's v1.2 fix behaving exactly as designed** — a
checker structurally unable to print VERIFIED without proof.

**The ordering matters and is part of the fix.** The pin list depends on the Register *and* on the
manifest that pins it — the generator refuses to run unless the Register hashes to the manifest's
CURRENT row (F-110). So it cannot come before A7; it must come **after**.

**Fixed:** the close-out routine gains **step A8 — regenerate the live-pin list**, run after the
manifest, and the list is regenerated here from Register v5.26 with `register_pin_verified: yes`.

> **RULE: a derived artefact must be rebuilt in the same routine that changes its source.**
> *"Someone did it last time"* is narrative. Only a numbered step is procedure.

**What the session says about itself.** Five findings came from building the next thing on the last.
Two came from **the owner looking at his own system through his staff's eyes** — and those found the
one thing five layers of gates could not, because every gate was checking that the code did what the
record said, and the record itself was wrong. **The eighth came from the owner running the
verification the routine is supposed to end with** — and it found that the routine does not, in
fact, end with it.

---

## §7.1 (continued) — S189 · F-135 · F-136 *(raised and appended the session they were found)*

Two findings, and neither came from a failure. **F-135 came from doing what the backlog said and
checking first.** **F-136 came from reading the untracked list that `verify_live_pins.py` prints at
the bottom of every run and that nobody has ever had a reason to read.**

### F-135 — a remediation instruction named three pages; two of them do not carry the thing it asked to assert · FIXED in the build (kit `S189_G1a`)

**What the record said.** HANDOFF_RUNBOOK v124 §2 ⭐1, and START_HERE_SESSION_189 §A repeating it:

> *"Add the design-fingerprint assertions (`--surface-page:#f3f2ee`, `id="toTop"`, `class="kick"`,
> the folded-help block) to the served-HTML checks for `approvals`, `workbench` and `review`; the
> entry page already has them."*

**What the files said.** Surveyed on the real bytes — recovered by hash from the kits, because the
repo's `finance/` tree is seven builds stale (F-97 part 2) — before a line of the fix was written:

```
/finance/entry      4/4 markers    S188_D2a
/finance/approvals  4/4 markers    S187_H1c        <- the instruction was right about this one
/finance/workbench  0/4 markers    S187_M1a
/finance/review     0/4 markers    S179
```

**Two thirds of that instruction would have gone RED at its own gate.** Not because the pages had
drifted, but because they were never under the design language at all: `Clinic_Design_Language_v1`
was born at kit `S187_H1b`, *after* the workbench build, and the review page has not been touched
since S179 — nine sessions.

**Why it happened.** F-130 was found and written up at the close, from the *shape* of the problem
("a page can revert and the gates stay green"), and the remediation named the pages the shape
applied to rather than the pages that had the markers. Nobody opened them. **That is F-132's exact
shape one document over**: *"add this assertion to those three pages"* is a claim about those three
pages, and it was recorded as a task rather than tested as a claim.

**Why it did not cost anything this time.** Only because the fix was built by someone who surveyed
first — the F-133 habit, applied to a page instead of a table. Had the instruction been implemented
as written, the installer's own gate would have caught it (that is what the gates are for), but the
cost would have been a red install and a rebuild rather than ten minutes of `grep`.

**The fix, and why it is bigger than the instruction.** `S189_G1a` does not assert v1 on the two
pre-v1 pages. It declares the **measured** state of all four served pages as a table, and asserts it
in **both** directions — the two pre-v1 pages are asserted NEGATIVELY, so that rebuilding either one
under the design language cannot land silently either: it has to come back to the table and flip the
flag. A one-directional assertion would have closed F-130 for two pages and left the other two
exactly as blind as before.

> **RULE: a remediation instruction is a claim about the thing it names, and carries the same burden
> of proof as any other claim.** A finding's *diagnosis* being right does not make its *prescription*
> tested. Write the fix against the files, not against the finding.

### F-136 — the manifest keeps its own copy of a value it says the Register owns, and nothing checks the copy · OPEN, fix specified

**What was found.** `verify_live_pins.py` prints, at the foot of every run, the live code the record
never mentions. It listed `/root/wa/staff_ledger.py`. Chasing that produced three values where the
canon should have had one:

```
/root/staff_ledger.py       92665b64f015fee9302ac3da6100f5c8   Register v5.26 pins exactly this;
                                                               the checker MATCHED it on the box
/root/wa/staff_ledger.py    06bf03cb74e84959e33dbe83b3c311de   appears NOWHERE in the repo
manifest Tier-2 row         74dac84eb15f5172478a97066f56c99d   matches neither file on the box,
                                                               and is absent from Register v5.26
```

**The record is right about the live file.** `staff-ledger.service` runs
`/root/wa/venv/bin/python3 /root/staff_ledger.py serve`, and that file hashes to the Register's pin.
The stray in `/root/wa/` is wired to nothing — no service, no cron. Backlog ⭐4's ₹70,000 will
therefore be read off the file the canon knows about, which is the question that made this worth
chasing at all.

**The fault is in the manifest, and it is structural rather than clerical.** The Tier-2 Attendance
row reads: *Staff Ledger app `staff_ledger.py` **v2.4 `74dac84eb15f5172478a97066f56c99d`**
(separate live system, **Register-tracked**)*. It **names the Register as the authority and keeps a
copy of the value anyway.** The Register advanced at S162/S164; the copy did not.

**Why nothing caught it in twenty-seven sessions.** Two checks run at every Phase 0, and this hash
falls between them:

- `gen_live_pins.py` builds the pin list **from the KB Register**. A hash that lives only in the
  manifest never enters the list, so **`verify_live_pins.py` has never once looked at it.**
- Phase 0's F-88 cross-check asks of each manifest token *"is this a document in the repo?"* and
  correctly answers **no** — it is a live-code pin — and stops there. It never asks whether the pin
  is **true**.

**A hash present in the manifest but absent from the Register is checked by neither.** It has been
unverified since S162, and it announced nothing, because Tier 2 is hash-verified and never read
(D34/D247) — the discipline that protects frozen products is also what hid this.

**The fix.** Strip the md5 from that row and leave the pointer. A document that defers on a value
must not also carry it; keeping a copy is how the copy goes stale. The same sweep should check every
other manifest row for a duplicated live-code hash. Kin: **F-116** (a phantom hash in the linchpin's
own footer — *"a hash is transcribed from a file or it is not written"*), and the **F-45/F-108**
family of stale self-reference.

> **RULE: duplicate a value and you have created a second thing to keep true.** If a row says
> another document owns a fact, the row may point at it and may not restate it.

---

## §7.1 (continued) — S189 build · F-137 · F-138 *(raised and appended the session they were found; both closed the same day, live)*

### F-137 — the record diagnosed an overstatement that never existed · FIXED + INSTALLED (kits `S189_W1a` · `S189_W1b` · `S189_C1a`)

**What the record said.** Runbook v124 §2 ⭐0b, the manifest's S188-POST block, and F-133's own entry:
*"cash in hand is overstated by unbooked handovers … the ledger is overstated by whatever is genuinely
with the two doctors and no record exists to net it down."* The prescribed close: *"enter the handovers
retrospectively"* — and the only handover table the S188 card read was `cash_movement`.

**What the schema says.** `v_day_cash` computes `cash_out_p = SUM(cash_movement WHERE
direction='out')` and `v_cash_ledger` subtracts it from closing. **Every movement row reduces cash in
hand, whatever its party.** Entering the handovers as prescribed would have cut cash in hand from
₹2,05,198 to about ₹30,000.

**What the count says.** S186, 17 Aug 2026, notes counted: drawer 0 · owner ₹18,963 · Dr Bhawna
₹1,56,235 = **₹1,75,198** — exactly the books once Darpan's ₹30,000 is entered. **There was no
overstatement.** The money never left the business; it is located with the two doctors. And the custody
facts HAD been recorded — as a sentence in `cash_count.explanation`, written in the same session that
created `cash_custody_event` to hold them. No query reads prose, so the card said zero and the backlog
spent two sessions aimed at a phantom.

**The owner's ruling, S189 (recorded, not assumed):** cash held by either doctor IS cash in hand,
merely located elsewhere. Custody is LOCATION; movement is QUANTITY.

**The fix, in three kits, all live the same day.** `S189_W1a`: the card reads `cash_custody_event`
(which no ledger view touches), places (`drawer`/`counter`/`bank`) are never shown as parked *with*
anybody, and the payload carries the count it rests on; six new checks prove the two-sided property —
a custody event moves the card and not the ledger, a movement moves the ledger and not the card.
`S189_W1b`: F-138's correction (below). `S189_C1a`: the counted position recorded — four rows totalling
₹1,75,198 to the paise against `cash_count`, the ₹1,45,000 balancing entry admitting in its own note
that its individual journeys are unitemised, the drawer's ₹0 recorded by writing nothing. The gate
restored-on-red unless `day_line`, `cash_movement`, `cash_adjustment`, `day_expense`, the ledger net
AND cash in hand were all byte-identical. On the box: cash ₹2,05,198 → ₹2,05,198, custody 0 → 4 rows,
entered total = the count, smoke 488/488.

> **RULE: a diagnosis in the record is a claim about the schema, and the schema is read before the fix
> is prescribed.** The third F-132-shaped claim found this session (after F-135 and the "already
> correctly scoped" original) — and the first one aimed at the books themselves.

### F-138 — three state-asserting checks refused the migration they were written to protect · FIXED + INSTALLED (kit `S189_W1b`)

**What happened.** The first C1a run was perfect until its final step: precheck green, migration
applied, verify green — *"cash in hand Rs 205,198.00 → Rs 205,198.00 UNCHANGED, as promised"* — and
then the full smoke suite went red on three checks and the installer restored the whole database. An
honest red, behaving exactly as built.

**The fault was in the checks, written earlier the same session.** *"Parked with Dr Manoj must be
Rs 0.00"* · *"custody inside this year must be exactly Rs 12,345.00"* — true of a store with no custody
rows, false the moment `S189_C1a` legitimately recorded that the owner holds ₹18,963. The F-106/F-125
family: a state-asserting test, broken by the first real datum. **The aggravation:** the fourth check
in the same block had already been converted to a delta during the build, citing F-106 in its own
comment, while its three neighbours were left absolute. The discipline was applied to the line under
the cursor, not to the block.

**The fix.** Every assertion measures the delta its own inserts produce (`_paise` on the store's prior
position), rehearsed offline green on BOTH store states, and the old app rehearsed RED on a migrated
copy with exactly the box's three FAIL lines — the failure reproduced before the fix was claimed.

**The count-equal problem, met honestly.** 488 → 488: checks corrected, not added, so a check count
cannot see this kit (F-130's blindness in a new coat). The installer therefore proves itself by
reproduction: it applies the C1a migration (hash-verified, D188) to a throwaway copy of the live store
and requires the CURRENT app red with every FAIL naming F-137, the NEW app green on that copy, and the
NEW app green on live — all before any swap. On the box: 485/488 reproduced, then 488/488, 488/488.

> **RULE: when a rule is applied to one line, it is applied to the block. And a fix whose effect a
> count cannot see is proven by reproducing the failure it cures.**

---

## §7.1 (continued) — S189 expense menu · F-139 · F-140 *(raised and appended the session they were found; both closed the same day, live)*

### F-139 — a dropdown that pointed at nothing · FIXED + INSTALLED (kits `S189_E1a`/`S189_E1b`)

**How it was found.** The owner, reviewing the ₹30,000 walkthrough: *"this free text entry will
become the rogue spoiler — do some dropdown selection flow."* Reading the existing control before
designing its replacement found that a dropdown already existed, and that its staff selector was
hardcoded: ids 1 and 2, `staff_ref` empty since S179, nothing in the app reading or writing it,
*"Someone else"* a fake staff member. The free-text zoo, surveyed: 46 `legacy (uncategorised)` + 6
`legacy (unreadable)` + 3 `Salary advance - Darpan` — Darpan has essentially never typed a free-text
expense; the rot was all import-era. **Zero rows ever carried a staff_id: the fake ids were never
exercised.**

**The fix.** The owner ruled the staff selector out of existence — on the medical page a salary
advance is Darpan's own — and the server now resolves the identity at write time, creating the one
real row lazily; client ids are ignored, old-page shapes accepted but their ids discarded. The menu:
Medicine purchase · Shop expense · Transport/courier · My salary advance · Other (details required).
One authored source; the served page is held to every label; a skipped choice is refused, never
written as an uncategorised row. The advance writes `Salary advance - Darpan` — the exact S184
string — so the whole history remains one queryable value.

**Named, deliberately not fixed (scope):** a re-saved draft silently drops its earlier expenses
(`loadDay` never repopulates the repeaters; the save is full-replacement — live since S179), and the
future D3 bridge must reconcile `PENDING_LEDGER_WIRING` rows against manually-entered ledger rows
before posting anything.

> **RULE: a dropdown is a claim that its values exist. Attribution is the server's to decide.**

### F-140 — the rehearsal store had the schema and not the shape · FIXED + INSTALLED same day (kit `S189_E1b`)

**What happened.** `S189_E1a` reached the box and was refused by its own installer: staged smoke
499/505, six FAILs, nothing swapped. The projection had said +21; the gate held it to that promise.

**The mechanism.** The new selftest block hunted a free rehearsal day forward from 1 April. The
offline seed store is continuous, so offline the hunt ended at 14 August and everything passed. The
live store's first free date is a Sunday in early April — Sundays are optional days (D322), the
legacy import never filed them — **135 days back, beyond the 120-day backfill window**, where
`api_save_day` answers `too_old` before the expense parse. All six checks failed identically,
including three that should have been immune, which was itself the clue: the failure had to precede
parsing.

**Diagnosed by reproduction.** A copy of the seed store given a beyond-window gap (5 April deleted)
produced **exactly the box's six FAILs**. A mid-window gap (4 May) produced only three — the
refusal checks parse before the closing guard and passed. The difference discriminated `too_old`
from `negative_cash` mechanically, with no argument needed.

**The fix, and the second lesson inside it.** The finder now searches backward from today — the
direction the D2/F-129 blocks already used, *a rehearsal must stand where the maker is allowed to
stand* — and every check embeds the server's actual error in its label (`got %s/%s`), because six
bare reds cost a reproduction that a single printed error would have made free. Rehearsed green on
four store shapes — continuous · mid-window gap · beyond-window gap · custody-migrated — before the
kit was reshipped. On the box: 488/488 → 509/509, +21 exactly.

> **RULE: a rehearsal store must carry the live store's SHAPE — its holes, not just its tables.
> And a check that can fail must say why.**

---

## §7.1 (continued) — S190 · F-141 … F-146 *(raised at S190, RULED and appended at S191)*

> **Why these landed one session late, stated plainly.** All six were found during Session 190 and
> every one was **recorded, not minted** — in the KB Register's fold blocks, in Archive §S190 and in
> Runbook v126 §2 ⭐2 — because the project's convention is that the owner rules on what earns a
> number. Nothing was owed and nothing was lost; the Fault Register stayed at v2.29 by design, and
> said so. At S191 the owner ruled that the call was the assistant's to make. **The ruling: six
> candidates, five numbers, one fold** — the delivery-note path (candidate 2) is recorded inside
> F-141 as its second instance rather than minted separately, because it is the same fault with a
> different coat, in the same session, from the same root: a value written from narrative or memory
> where the record was sitting in reach. Inflating the count would have made the family history less
> legible, not more.

### F-141 — a fabricated hash tail, and a path written from memory · CLOSED (kit `S190_E2` v2)

**What happened.** The `S190_E2` installer carried a currency-gate constant for
`finance_entry_clinic.html`: a full 32-character md5 whose head was the record's truncated
`0c64fda2…` and whose tail had been **composed to fill the remaining width**. No file in the project
has ever hashed to that value. The D317 chain compared it against the live bytes, refused at step
[2/7], and stopped with nothing swapped.

**What the refusal then proved.** An on-box `tr -d '\r'` comparison established that the *payloads*
had been built on the exact live file — only the installer's constant was wrong. Kit v2 changed that
one constant, transcribed from the owner's own `md5sum` run on the box. Live smoke landed 509 → 542,
+33 exactly.

**The part that matters.** The correct full value **had been sitting in the live-pin list all along**.
The mistake was reading a narrative prefix as though it were a pin. The Register's live-file table is
the source; the prose around it is a pointer to that table and nothing more.

**The second instance, same session, same root.** The same kit's delivery note gave the install path
as `/root/deploy` where the box uses `/root/deploy/repo` — written from memory rather than read off
the record, and caught only because the owner ran it. It is folded here rather than given its own
number: one fault, two coats.

**Family.** F-109 (an invented hash), F-116 (a phantom hash in the linchpin's own footer), F-135 (a
remediation instruction written about files nobody had opened). **What is new is the venue.** This
family had lived only in documents, where a wrong token is a provenance problem. It has now reached
an **installer's gate**, where a wrong constant is load-bearing — and the only reason it cost nothing
is that the gate compares against reality rather than against the record.

> **RULE: a hash is transcribed from a measured value or it is not written. A narrative prefix is a
> pointer, never a pin. A path in a delivery note is read off the record, not recalled.**

### F-142 — the harness read the wrong line and could not tell · FIXED (kit `S190_F3` v2)

**What happened.** `S190_F3` v1 was refused by its own installer. The refusal itself was correct
behaviour, but the reason was not the payload: the harness ran the selftest and took **`tail -1`** as
the summary line, and on that run the last line of output was a failing check rather than the
summary. The installer therefore could not distinguish *"the suite failed"* from *"I read the wrong
line."* Nothing on the box moved.

**The fix.** v2 changed the harness and only the harness: it greps the **whole** output for the
summary line, and requires the expected fail-set **by name** rather than by position. The payload was
untouched between v1 and v2. F3 then landed count-equal — 547 → 547 — and proved itself by
reproduction on the box: 545/547 with exactly two fails, both naming F3, then 547/547.

**Why this earns a number rather than a note.** An ordinary bug produces a wrong answer once. **A
verification harness that can misreport its own verdict corrupts every result it will ever produce,
including the ones that pass** — and it does so invisibly, because a harness is the thing nobody
double-checks. Kin: F-122 (a checker printing a claim it had not tested), F-124 (a publisher printing
success over a swallowed fatal).

> **RULE: a harness that reads "the summary" must first prove the line it read IS the summary. Grep
> the whole output; name the expected failures; never `tail -1`.**

### F-143 — the quota counted history as though it were now · FIXED + INSTALLED (kit `S190_SL3`)

**What happened.** D331 shipped a per-staff monthly advance ceiling with the month-to-date total shown
inline. The counter summed every `ADVANCE_ISSUE` row by calendar month. **The S155 migration rows
carry years of loan history and are dated August 2026** — so Darpan's line read *"Rs 3,63,000 of Rs
15,000"*, and the gate **would have refused his ordinary, wholly legitimate ₹15,000 advance.**

**Why no rehearsal could have caught it.** The offline store has no migration rows. F-140 taught that
a rehearsal store must carry the live store's *shape* — its holes, not just its tables. This is one
layer further out: **the shape here is historical data whose dates mean something other than what they
say**, and no seeded store reproduces it. The owner's first live look at the feature found it in
minutes.

**The rulings, executed the same hour.** The quota counts **from the D331 install forward**:
pre-install rows are grandfathered — fully visible in the position card and the statement, recovering
as normal, but never eating a month's quota. And **interest-bearing loans never consume the ordinary
quota**, bypassing its gate entirely, because a loan is the parallel D250 instrument with its own
recovery machinery. Selftest 212 → 214, +2 exactly. *(The application requirement on a NEW loan stays
procedural — wiring it would break the migration path. Recorded in the D331 contract, not hidden.)*

> **RULE: a counter over dated rows must ask what the date MEANS, not only what it says. A policy gate
> meets its real data on the box before it is trusted anywhere.**

### F-144 — identity read from the broker, not the unit · FIXED + INSTALLED (kit `S190_F4`)

**What happened.** The medical save's approved-day guard tested `u["role"] != "checker"` — the **SSO
broker** role, legacy header semantics — instead of the unit roles that `require()` had already
computed one line earlier. Through SSO the owner's broker role is `doctor`, not `checker`, so the
screen refused him with *"This day is already approved — only the doctor can change it"* — **shown to
the doctor.**

**How long it had been there.** The clinic twin has carried the correct unit-roles form since S182.
The medical twin never did. It survived because **nobody had ever re-edited an approved medical day**
until that hour: a defect live for sessions, held harmless only by a door no one had tried.

**The fix, and the audit that came with it.** One functional line; two new checks reproduce the
owner's exact SSO shape so the case cannot regress unseen. An audit of **every** `u["role"]` use in
the file found this the only wrong one — which is the part worth keeping, because the value of finding
one instance of this family is the sweep it licenses. Live smoke 547 → 549, +2 exactly.

**Family.** F-84 (identity taken from the layer easiest to reach rather than the layer that is
authoritative) and F-127 (a role gate on the surface is not a role gate on the data).

> **RULE: when a broker sits in front of a unit, identity comes from the unit layer. And the moment one
> `u["role"]` is found wrong, every one of them in the file is audited.**

### F-145 — a queue that hid a class did not un-hide a row that left it · FIXED + INSTALLED (kit `S190_F5`)

**What happened.** The approvals queue deliberately hides days marked `source='legacy_sheet'`, so the
bulk pre-15-Aug import cannot flood it. The owner edited his 31-July day. The edit made it an app
entry in every sense that mattered — **its ₹10,000 counted in the drawer immediately** — but the
`source` marker still read `legacy_sheet`, so the day **disappeared from the approvals queue while its
money was already live.**

**The fix.** A correction now re-marks the day `source='app'` on both units; the `day_revision` keeps
the legacy original verbatim, so nothing about the import's history is lost. Live smoke 549 → 550, +1
exactly. The day was then filed and approved through `/finance/review`.

**The shape worth naming.** A filter written to protect a queue *from a bulk import* had quietly become
a filter that **hid real work awaiting approval**. The hiding rule outlived the condition it was written
for, and nothing re-examined it — the classification was set once, at import, and treated ever after as
a permanent property of the row rather than a statement about how it arrived.

> **RULE: a queue that hides a class must un-hide a row the instant it leaves that class. A
> classification used as a filter is maintained by every path that can change the class.**

### F-146 — a refusal that looks like a save · OPEN (rule adopted; UI fix owed, not built)

**What happened.** Before SL3 landed, the owner entered two of the sitting's advances. The
migration-dated quota gate (**F-143**) refused both — correctly. The refusal did not read as a refusal
on the screen in front of him. **Both the owner and the assistant then carried "the advances are in"
forward as established fact**, and the belief survived until `/ledger/book` was queried directly and
proved absence. The entries were re-made, walked through, and confirmed in the book.

**What was and was not damaged.** Nothing was corrupted: the gate was right, the money never moved,
the books were never wrong. **What was damaged was the session's model of reality** — for a stretch,
work proceeded on a false premise, and no artefact anywhere would have contradicted it. Only a query
against the store dislodged it.

**Why it is not a bug in any one place.** The gate behaved exactly as designed. The page rendered
without error. No exception escaped, no log went red. The fault is that **a refusal and a success were
not distinguishable at a glance**, and that neither party verified against the store before believing.
That is a UX property and a discipline, not a defect with a line number — which is precisely why it
would have been lost if it had not been given one.

**Status.** OPEN. The discipline was adopted immediately and is now standing practice (Runbook v126
§1.3): every entry in the remainder of the sitting was confirmed in the book, not on the form. **The
UI fix — making a server refusal impossible to mistake for a save on the ledger's entry form — is
specified as owed and has not been built.**

**Kin.** F-132 (a claim about a screen nobody had opened) and F-124 (success printed over a swallowed
fatal): all three are cases where **the system's report of what happened diverged from what happened,
and only looking at the real thing closed the gap.**

> **RULE: verify entries in the BOOK, never on the form. A refusal must be impossible to mistake for a
> save.**


## §7.1 (continued) — S191 · F-147 … F-151 *(raised and appended the same session — found by confirming the live system against its own signed rulings, not by any failure)*

### F-147 — the close records recovery the salary could not pay · OPEN (ruled BUILD)

The owner asked for confirmation of the staff advances system. The confirmation was done on the box:
the SL4 kit payload hashed to the live pin, the selftest ran 218/218 in the owner's own terminal, and
every D331/SL3/SL4 clause was read in the live bytes. All of it held. Then the first real month-end
was PROJECTED rather than awaited: the July-attributed ₹10,000 and the August ₹15,000 both collect at
the August close (first close ≥ their month), plus the loan's ₹5,000 — **₹30,000 against a ₹20,000
base**. `compute_salary()` has no floor; the quota lane writes `ADVANCE_INSTALMENT` for the entire
balance unconditionally, "balance after: 0". Had August run, ≈₹14,000 of repayment would have been
recorded that no money ever paid. **D250 had already ruled the missing behaviour** — "if salary can't
bear all, the instalment skips and the tracker prices it" — in the workbook era it was a human
judgment applied by hand; the migration carried the arithmetic and left the judgment behind. **RULE:
when a manual system becomes a machine, its written judgment clauses are requirements, not
commentary.** Fix: the D332 capacity rule (S192_SL6).

### F-148 — the drawer→ledger bridge was never built, and the code knew · OPEN (ruled BUILD AND TEST)

Surveyed, not assumed (F-133's habit): `finance_app.py`'s approval path writes
`ledger_ref='PENDING_LEDGER_WIRING'` with the comment *"B6 wires the real Staff Ledger call. Until
then this records intent explicitly rather than pretending the posting happened."* The honesty is to
its credit — and it is also a two-session-old IOU that outlived its own plan: B6 was D329 machinery,
D330 superseded D329 whole, and the bridge fell with it while the need did not. Every pharmacy-drawer
salary advance since has reached the ledger only because the owner typed it there. The 17-Aug ₹15,000
is in the book solely by the owner's own hand; the Apr–Jun ₹40,000 rows still carry `ledger_posted=0`.
**RULE: when a decision is superseded WHOLE, every dependency that pointed into it is re-homed or
explicitly re-owed — a superseded decision's debts do not pay themselves.** Fix: D332 §2.5, the
request-not-draw flow (S192_F6) — one approval writes both books, and cash cannot move without it.

### F-149 — the route the ruling built can never fire · OPEN (ruled CORRECT)

D250: two skips per FY; "3rd onward auto-flags recovery from perks." The live `skip()` hard-refuses at
the limit — the flag path was never written, so the ₹19,000 of recorded perks is unreachable by the
mechanism designed to reach it. Same family as F-147: arithmetic faithful, judgment unbuilt.
Superseded in shape by D332 §2.1 (defer with a waivable 3rd-defer penalty on loans only); corrected in
S192_SL6.

### F-150 — the policy start-date lived in narrative, and the machine deducted anyway · OPEN (ruled BUILD AS SETTING)

S151's record states twice that July 2026 is pre-policy: Deduction/Incentive columns "PREVIEW ONLY
(policy starts August)". The live July salary applied both — every one of twelve staff over-deducted,
**₹16,552.38 in total**, Darpan alone ₹3,933 — because the start-date was two sentences in a session
narrative and no file the machine reads carries it. The owner's instinct ("july no ded") was not
leniency; it was enforcement of his own standing ruling, which nothing had honoured. **F-134's shape
one layer up: a derived artefact must be rebuilt by the routine that changes its source — and a
POLICY must live where the machine can read it, or the machine will contradict it.** Fix: enforcement
dates as settings, unlocked by the notice-served date (the notice is not yet shared — no promise
outstanding); August ruled preview-only too; the July remediation rides the owner's sheet-close.

### F-151 — the prohibited word is on the screen · OPEN (ruled CORRECT)

D250, statutory caution: deductions are framed as attendance-based half-days, "never 'fines'". The
live salary table's column header is "-fines"; the salary page says "Rs 50 fine on an absence".
Found while transcribing the live table — the exact prohibited word, in the artefact staff see, since
the salary layer went live. Wording only; no rupee moves. Fix in S192_SL5.

> **The session's shape, for the record:** none of these five was found by a failure. All five were
> found because the owner asked for CONFIRMATION and the confirmation was performed against the live
> system instead of the record — F-135's rule applied at scale. The system that was confirmed came
> through intact; what the reading surfaced was the distance between D250's written judgment and the
> machine that had faithfully implemented only its arithmetic.

### §7.1 (continued) — S192: four CLOSED, three minted (F-152 … F-154)

**F-147 — CLOSED (S192, `S192_SL6`).** *"The close records recovery the salary could not pay."* D250's
judgment clause — *if salary can't bear all, the instalment skips* — is now built. **The capacity
rule:** one budget per staff per month = base − other debits already booked − a protected
`min_takehome` setting, spent by every recovery lane in order (schedule → quota → waterfall). What
cannot be taken is written as a **`CAPACITY_HOLD`** row and **stays owed** — never silently dropped,
never quietly recovered against money that does not exist. **No base salary on file DISABLES the
gate** rather than freezing every recovery: the D331 fail-open design, and the degradation is shown,
not silent. The projected August close that started this finding — ≈₹14,000 of repayment recorded
that no money paid — can no longer happen.

**F-149 — CLOSED (S192, `S192_SL7`).** *"The perks-recovery route can never fire."* Answered from the
other end, per D332 §2.9: rather than force a recovery path nobody wanted, perks became **readable**.
`/ledger/perks` gives a net-total index across staff, a per-staff view with the lifetime figure and a
year filter, and append-only honesty — a contra'd perk nets to zero with **both rows still visible**,
because a contra is simply a negative PERK row and needs no special case. The real defect was never
the recovery branch; it was that a perk could be **entered and then never read**.

**F-150 — CLOSED (S192, `S192_SL5`).** *"A policy start-date living only in narrative was missed by
the machine that had to obey it."* Enforcement is now a **setting**: `ledger_settings.json` carries
`attendance_enforce_from` — the notice-served month — and while it is unset **every month is
PREVIEW-ONLY**, with attendance-policy deductions rendered struck-through and **not applied to NET**.
Ledger money still applies, because it is owed rather than a penalty. July and August are therefore
preview by construction rather than by anyone remembering. `sunday_enforce_from` and
`incentive_rungs` ride the same mechanism, so the ladder can shift without touching code.

**F-151 — CLOSED (S192, `S192_SL5`).** *"The live system says the prohibited word."* Every rendered
"fine" for an ATTENDANCE deduction now reads **"attendance deduction"** — the salary column header,
the two statement rows, the help text and the `SALARY_PAID` narration. Scoped by the owner to
attendance only: the ledger's **uniform / i-card / ad-hoc** charges keep their names, being genuine
charges rather than wage deductions, and the attendance-report CSV column names are untouched because
they are an interface contract.

**F-148 — STILL OPEN.** The drawer→ledger bridge. `S192_F6` is **designed and deliberately not
built**: `finance_app.py`'s 550-check smoke suite opens with `shutil.copyfile(live_db, tmp_db)` — it
runs against a copy of the real `finance.db`, which exists only on the VPS, so it **cannot be run
offline at all**. Shipping into it on reasoning alone is **F-87** precisely, whose own RULE is that
making an unrunnable suite runnable is the FIRST task. The survey did establish that F6 is narrower
than feared: the inline ceiling refusal already exists, and the approval endpoint already carries
`# Approval is what posts a salary advance to the Staff Ledger. Not entry.` with the call stubbed as
`PENDING_LEDGER_WIRING` — the codebase being honest about its own gap instead of pretending. Design
filed as `S192_F6_Design_and_Survey.md`. **A cross-book money writer is the last thing that should
ship on a plausible argument.**

---

### F-152 (S192) — the files that GATE an install were never given the install's own line-ending discipline
**Raised:** S192 · **Severity:** medium (install integrity) · **Status:** CLOSED the same session
**Kin:** F-100 (the `.gitignore` blanket that silently dropped a kit file), D164, D316

**What happened.** A routine `PUBLISH_ALL` run printed:

```
warning: in the working copy of 'deploy_kits/S192_SL6/KIT_ID.txt',
         LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'deploy_kits/S192_SL6/SUMS.md5', ...
```

`.gitattributes` pins `*.py`, `*.sh` (D164) and `*.html`, `*.new`, `*.sql` (S189) to `eol=lf`. It has
**never pinned `*.txt` or `*.md5`** — the two extensions that carry a kit's **checksums and its
identity**, and the extension of `live_pins.txt`, which `verify_live_pins.py` reads on the VPS.

**Why it matters, and why it is not cosmetic.** A `SUMS.md5` committed with CRLF makes `md5sum -c`
read the filename as `staff_ledger_X.py\r`, fail to find it, and **refuse a perfectly good kit at
gate [1/6]**. That is a gate firing **wrongly** — and **D316** already established that a halt which
fires on good input is worse than no halt, because it is the halt that gets waved through, taking the
real ones with it. Nothing had broken: the blobs committed as LF and the VPS checkout was correct.
**The warning was the finding.**

**Fix.** `*.md5 eol=lf` and `*.txt eol=lf` added, with the reasoning written into `.gitattributes`
itself rather than into a session note — narrative is not procedure (F-134). **RULE: the files that
GATE an install are part of the install, and inherit its line-ending discipline.**

---

### F-153 (S192) — a contra does not carry the original's attribution, so reversed money keeps eating its month's quota
**Raised:** S192 · **Severity:** medium (a gate that can fire wrongly) · **Status:** OPEN, one line
**Kin:** D331 (the quota), F-143 (the migration-dated quota), D316

**What happened.** `make_contra` builds the reversing row from the original — category, staff, dates,
the negated amount — but **not `against_month`**. `advance_month_taken()` counts only rows carrying
an explicit `against_month` (the SL3 grandfathering), so **the original still counts and its contra
does not**: a reversed advance goes on consuming the month's quota for ever.

**Measured, not theorised.** During the S192 data corrections, reversing Darpan's ₹15,000 (against
August) and entering the consolidated ₹20,000 would have made August read **₹35,000 taken** against a
₹10,000 ceiling. The consequence is not a wrong balance — the money is right — but a **future
above-ceiling refusal firing on money that has already been reversed**, i.e. the D316 shape again.

**Handled, not fixed.** The correction script stamped `against_month` onto each contra row, and the
dry run showed it before it ran; August then read the correct ₹20,000. **The gap in `make_contra`
itself is still open** — one line, adding the original's `against_month` to the contra row.

---

### F-154 (S192) — the assistant had a live bridge to the owner's machine and made him do the work by hand
**Raised:** S192 · **Severity:** low (owner's time, and trust) · **Status:** CLOSED by practice
**Kin:** F-135 (a claim written without opening the file), F-141 (a value written from narrative
rather than the record) — the toolchain, not the canon

**What happened.** The first kit of the session was delivered as a chat download with instructions to
save, unzip into the repo, and publish. It failed three times: once because the instruction contained
a literal **`…/deploy_kits/…`** placeholder that the owner reasonably pasted verbatim as a path; once
because the zip had never been downloaded, so `PUBLISH_ALL` correctly reported *"nothing new to
commit"* and the VPS correctly reported a file that did not exist; and once more before the cause was
found. **The session had a connected bridge to the owner's PC throughout.** Once the files were
written **straight into `deploy_kits/` through that bridge**, every subsequent kit landed first time.

**Why it is recorded.** The VPS was behaving correctly at every step, and so was git; the fault was an
assistant that reached for the manual path while holding the automatic one. It cost the owner several
minutes of pasted commands and a fair amount of irritation, and it is the same family as F-135/F-141:
**acting from assumption instead of from what is actually available.**

**RULES.** (a) Before instructing the owner to do manual work, **check whether a connected capability
already does it.** (b) **Never hand over a command containing a placeholder that looks like a path** —
if a path is not known, find it or ask, but do not ship an ellipsis into a terminal.

---

### §7.1 (continued) — S193 · F-155 … F-159 *(raised, fixed and closed the session they were found; folded into this register at the S197 fold-in — the append itself was owed from S193, the F-108 condition cleared here)*

**F-155 (S193) — "✓ applied" with empty books.** The 17-Aug Marg push read **applied** while the day carried no ingested bills: the push had fired before the day was filed, `ingest_day` answered `still_not_filed`, and the run was marked applied anyway — its payload pruned, unrecoverable. The status now tells the truth (applied ⟺ every carried day ingested; otherwise `pending`, payload KEPT), which is also what made the S194 auto-replay possible: a pending push with its payload intact is simply replayed the moment its day is filed. The pre-F-155 pruned payloads (17/18/19 Aug) were re-ingested at S195 from the medical-PC `SENT\` folder — the system's own dated copies. **RULE: a status that says "done" must be derived from the outcome, never from the attempt — and a payload is kept until its work is proven done.**

**F-156 (S193) — the flag with no clearing path.** `MARG_DAY_NOT_FILED` was written at push time; nothing ever cleared it, so it outlived its truth. The display now self-heals (a day with a Marg batch hides the flag; no row deleted — the history stays). **RULE: any flag written by an event needs a defined clearing event, or a display rule that derives its currency.**

**F-157 (S193) — `NaN > 0` is false, silently.** The custody API returned Indian-comma-formatted strings; the client compared them numerically; every hand vanished; the box rendered empty **from the day it shipped** — and nothing complained, because an empty list is a legal render. Found only when the cash-position build re-read the same endpoint. **RULE: parse to number for maths, format for display — and a box that CAN legitimately be empty needs a check that distinguishes "empty" from "eating an error".** (The S196 class-refusing health check is this rule generalised.)

**F-158 (S193) — the window fault.** Subtracting today's reserve from every historical closing manufactured negative drawers back to mid-July — before the reserve existed. The derived day-wise drawer now starts at the last clearing event. **RULE: a derived figure carries its valid window with it.**

**F-159 (S193, assistant delivery fault) — the cached GET.** Two rounds of "still broken" against a server that had been fixed on round one: Chrome served the API GET from its HTTP cache (cookie-clearing does not touch it). The fetch is now cache-busted, and the fix was verified by reading the live API in the owner's own Chrome BEFORE claiming it again. **RULES: (a) the browser is part of the system — any freshness-critical fetch is cache-busted; (b) before re-diagnosing a "failed" fix, verify what the client is actually receiving.**

### §7.1 (continued) — S196 · F-160 … F-162 *(raised at S196, two closed by kits the same session, one remedied the same hour)*

**F-160 (S196) — the kit outside the git tree.** The session's first kit was written to `D:\dr-manoj-git\deploy_kits\…` — the connected folder's root — when the repo actually lives one level deeper at `D:\dr-manoj-git\drmanoj-clinic-automation\`. `PUBLISH_ALL.bat`'s own first line names `REPO_DIR`; it was not read. The publish pushed a commit without the kit; the VPS pull found nothing; the owner's install failed with a missing path. Remedied the same hour: the kit `mv`-ed into the real tree and re-hashed byte-identical, the install then GREEN. Family: F-135 (a claim written without opening the file), F-141 (a value written from memory with the record in reach). **RULE: the publish destination is read from the publisher's own config, never assumed from a folder root.**

**F-161 (S196) — the headline nothing consumed.** S195 built `_health_headline()` explicitly *"for the portal tile"*; no caller ever existed. For a full session the health page could be red while the portal tile stayed innocent — precisely the Marg-401 crisis shape the function was written to close. Found not by a failure but by reading the live bytes when the owner asked whether the crisis lesson was fully handled. Closed by `S196_HLT2`: `tile-summary` carries `health_line` and the tile leads with the worst problem. **RULE: a capability without its wire is a claim — when auditing, grep for the CONSUMER, not the definition.**

**F-162 (S196) — the check that died politely.** `_health_state` set a local `today = dt.date.today()`; the A4 block called `today()`; the local shadowed the module function; **both** month-vs-Marg cards threw on every render since S195 and the card caught its own exception into a courteous "could not be read (…)" line. The S195 close had recorded the check as done — it was, briefly, before its own session's later edit killed it. Caught by the owner's FIRST real read of the page (the F-132 pattern: a human looking beats a green suite). Closed by `S196_HLT3`: the one-line fix, plus a smoke check that refuses the whole class — **no health card may ever be a swallowed Python exception**. **RULE: a check that displays its own exception has died, not degraded — and the suite must refuse the class, not the instance.**

### §7.1 (continued) — S197 FOLD · the F-series fork reconciled; F-163 … F-168 minted from the S194/S195 records

**The fork (F-108 family, live).** At the S192 close this register's next-free was **F-155**. The canon then went unfolded for four sessions: S193 consumed F-155 and minted F-156–F-159 in its standalone close docs; S194 recorded ONE candidate as *"F-160 (candidate, owner's call to mint)"*; S195 recorded five faults **unnumbered**; S196 — unaware of S194's candidate — wrote its three candidates as F-160–F-162 and then, at its close, discovered the fork and froze all bare F-numbers. **Resolution at the S197 fold (owner-delegated): every number already in circulation keeps its meaning.** F-155–F-159 are S193's; F-160–F-162 are S196's (verified: no S194/S195 doc used a bare F-160+ token — swept across the repo and project knowledge); S194's candidate is minted as **F-163**; S195's five faults are minted as **F-164–F-168**, because leaving findings recorded elsewhere but never applied to this register is the F-108 condition by definition. **Numbering is therefore not chronological across F-160–F-168 — recorded here, not silently reordered.** Full text for F-163 (the email agent's server-side-search rule), F-164 (the credit-note sign), F-165 (never assert against an unprinted shape), F-166 (the coverage witness), F-167 (the bundled-Python standard) and F-168 (the read-only medical share, OPEN) is carried in the §7 index rows above and, verbatim from the sessions, in **Archive §S194/§S195** and the named `S195_*` docs — the index rows here are complete statements, not stubs.

**Also reconciled at this fold:** **F-148** — CLOSED at S193 (kit `S193_F6`): the drawer→ledger bridge is live, built seeded-store-FIRST exactly as F-87's lesson required, and the smoke suite has run offline ever since (its differentials caught faults before the box at S196). **F-153** — CLOSED at S193 (same kit): `make_contra` now stamps `against_month`. Both rows above updated from OPEN, visibly.

---

### §7.1 (continued) — S197 post-fold · F-169 *(minted by the first pin run on the fold's own list; closed the same hour)*

**F-169 (S197) — the fold's one transcription miss, caught by the machine built to catch it.** The S197 fold consolidated ~12 pin moves from four sessions of close docs. One was missed: `S193_UX` had patched `/root/finance/finance_ui/finance_entry.html` in place (`bae2dd8983c8c3b886705a4f6b6d8dba` → `92477b068c67e28661b049b7f3385708`), recorded at the time in `S193_F6_Live_Pin_Record.md` — which the fold itself filed to `KB_canon_S197fold/filed/` — but the Register's live-file table was assembled by reading the sessions' *final-pins* summaries, and S193's close summary listed `finance_approvals.html` without restating `finance_entry.html` (the UX kit's second file). The owner's first `verify_live_pins.py` run against the new list reported **RED, drift 1**, naming the exact file, the recorded value and the measured value — and refused the verdict until reconciled. The measured value equals the S193 record byte-for-byte, so the fix is a record correction, not a box change (F-118: the box wins, and the correction cites both provenances). Fixed in Register **v5.42** the same hour; pin list regenerated; expected result GREEN match 45. **RULES.** (a) A fold harvests pin moves from every session's was→now pin TABLES by machine (grep), never from narrative summaries — a summary written for humans legitimately omits what a table never does. (b) A drift where the box's value matches a filed session record is a RECORD fault by default; correct the record from the box and cite both. 

---

### §7.1 (continued) — S198 · F-170 … F-173 *(raised and appended the session they were found; three closed the same day, one open on the owner)*

**F-170 (S198) — the probe judged a code nobody had ever measured.** The `S198_P1` v2 installer gated on HTTP 200/302 from `127.0.0.1:8090` after service restart. The box answers **301** (plain-HTTP redirect) — for the superseded bytes exactly as for the new ones; the S196 installer that inspired the step had only ever *printed* the code. The gate therefore rolled back a healthy install — the rollback machinery worked perfectly; the specification it enforced was fiction. v3: probes print, never judge; the serves-proof moved to where it is real — import the installed module and render the page through Flask's `test_client`. Standing rule minted: **an installer probe's expected code is measured on the box or it is printed, never judged.**

**F-171 (S198) — worst-first was a docstring, not a behaviour.** `finance_app.py`'s health checker had claimed worst-first ordering since S195; no sort existed on the checks list. Every render since had shown severity in construction order. The owner saw it on the live page in one look. Closed by `S198_H2` (`checks.sort` + culprits in the hero line) and folded into the smoke (674 → 680, which includes ordering checks that would have caught the claim).

**F-172 (S198) — the alarm that could not read a calendar.** The Marg-push age check measured raw days since the last push; the clinic does not file on Sundays; a fully-current system therefore went red every Monday morning ('Something is wrong'). Cried wolf at the exact person the page was built to reassure. Closed by `S198_H2`: `_sundays_between` subtracts non-filing days; the general rule — an age alarm counts expected-activity days, never calendar days.

**F-173 (S198) — one historical advice file may have paid the wrong accounts.** Building the B1 vendor master, every FY advice file's rows were transcribed via the Drive text route with per-file total verification (18/18 matched). The **April-2025** file alone shows its account-number column displaced relative to its vendor names. If the bank executed it as filed, one or more April-2025 payments went to another vendor's account. OPEN: the owner checks the April-2025 bank statement line-by-line against the master; confirmation escalates to its own incident. *(This is a finding about a source file, not about any system built this session — recorded so it cannot be lost.)*

---

### §7.1 (continued) — S199 · F-174 … F-177 *(raised and appended the session they were found; all four closed the same day)*

**F-174 (S199) — the exclusion-mirror drift.** `staff_ledger.py` and `salary_engine.py` each hold a `SALARY_EXCLUDED` set and the engine hard-checks equality at import — a guard built at D288 because "a silent drift there would mis-pay". S192's D332 build added `ADVANCE_DEFER` and `CAPACITY_HOLD` (both ₹0 schedule markers) to the ledger's set; no sweep touched the engine's copy. The guard did its job the first time the salary page was opened live at S199 — refusing to compute and blanking the Net/Old/Delta columns with the exact drifted set named in its message. The fix is one constant (both markers added to the engine's set, commented to their origin); the deeper rule joins §1: a fold that grows a category set must grep for its mirrors. CLOSED by `S199_SALFIX`, engine selftest green on the real ledger.

**F-175 (S199) — the checkbox that meant the opposite of what it stored.** Found from the data, not the code: August's grid held dress-improper ticks on 55% of duty days, and the single best-attendance staffer (0 absents, 4 marks) was ticked "improper" 21 of 23 days. The maker screen's column headers read bare "Dress" / "I-card" over an unlabeled checkbox; the schema stored `dress_improper=1` on tick. Reception had been ticking to record "dress OK". No money was ever collected on it (dress was held discretionary), so the loaded gun never fired. Owner ruling: August ticks = Yes; the UI now asks the question explicitly ("Dress OK?" Yes/No, only an explicit No stores a without-day); `migrate_dress_S199.py` zeroed August's flags (before=(88,74), after=(0,0), DB backup taken). CLOSED.

**F-176 (S199) — today counted absent.** `collect_month`'s month-to-date pass ran through the current day, so every staff member without a punch *yet* appeared absent — the owner saved Sheet 1 at ~06:00 and the 24th showed "A" for all twelve, inflating every absent count by one. The flow engine now sets its cutoff to yesterday for every computation and grid (past months unaffected). Caught by the owner's first preview — the "owner's eyes are a test tier" model earning its keep on the newest surface. CLOSED.

**F-177 (S199) — the scenario's labels claimed a month they weren't computing.** v1 of the deduction-scenario page hardcoded its column labels to "AUG"/"STRICT" and derived its slab from `limits_for(ym)` — so July rendered under an "AUG" label while silently using the September slab-5, and the extra-leaves deduction was absent from the page entirely. A coincidence sharpened the confusion: Alisha's July marks money (₹1,666.67) exactly equals her old-model extra-leave figure, making the mislabeled column read as a leave deduction. v2 labels every column from the slab it actually computes, carries both slab sets for any month, and includes the full leave component. CLOSED.

---

**F-178 (S200) — the mid-duty punch blindsight. OPEN.** The punch feed keeps EVERY punch
(de-duplicated, nothing lost), but the day computation uses only `first` and `last`: a staff
member who punches in 09:00, out 11:00, back 15:00, out 18:00 reads as a complete punctual
full day — four missing hours invisible while the punches proving them sit in the feed. Worse:
neither the day page nor Sheet 1 renders the punch count or sequence, so there is NO screen on
which this could be noticed (found by the owner's instinct: "some staff take few hours off
during their duty and dont return at the time told"). Fix queued (⭐1): surface the full punch
sequence per day and flag any mid-duty gap beyond a settable threshold — the data already
exists, no new hardware. Honest limit: only punches that happen can be seen; the walk-out
without touching the machine is the hole the selfie-GPS punch (design candidate) closes. OPEN —
build queued.

---

---

### §7.1 (continued) — S201 · F-179 … F-183 *(raised and appended the session they were found; three closed the same day, one closed by the agent build, one OPEN by choice)*

**F-179 (S201) — the outbox had no consumer.** The router verified every report, archived it by the
business date inside it, and stamped it "queued for upload" into `MargArchive\_outbox`. Nothing read
`_outbox`. The only uploader in the chain was a manual double-click on the medical PC's
`SEND_TO_CLINIC.bat`, last pressed on 22 Aug. **Eleven verified reports** — 2 purchase, 6 closing
stock, 2 expiry, 1 scrap-store — sat correct, hashed and undelivered, while the capture side, the
router and the archive all reported success. The owner's only symptom was a page that stayed empty.
CLOSED by `marg_gate.py` (client-side delivery state, cross-batch superseding by `span_key`, live
token resolution with a local cache, `os.replace` for state writes), driven by the existing 10-minute
pull. **Recorded with it, because it is the session's own worst moment:** the assistant asserted the
server deduplicated marg-push by content — it does not, and a second copy of 24-Aug was staged. The
claim came from expectation, not from reading the ingest path.

**F-180 (S201) — the supervisor could drift silently, and did.** See the §7 index row. The design
ruling is the substance: **a component that must not self-update must self-report.** The agent's
refusal to overwrite its own running file is correct and is kept; what was missing was any way to
SEE the consequence. Comparison is by md5 rather than by the `AGENT_VERSION` constant, because a
constant is a claim a file makes about itself and D188 applies to claims as much as to filenames.

**F-181 (S201) — nested `<a>`, and the shape no counting test could see.** See the §7 index row. Two
things are worth carrying forward. First, **the owner's own saved copy of the SERVED HTML found it** —
the second time in S201, and the same mechanism that found a doubled `</tbody>` at S187 P2a. Reading
what the server actually sent is a distinct check from reading what builds it. Second, the S198
assertions were not weak: they counted rows and counted clickable rows, and both counts were right.
**The defect lived in a dimension no assertion described.**

**F-182 (S201) — the page in no design register.** See the §7 index row. F-130 was built at S189
precisely so a page could not silently revert its design, and it works — for pages it lists. This one
was never listed. **The inverse question (what is NOT in the register?) is the same question F-107
minted for the manifest**, and it has now recurred one register over.

**F-183 (S201) — two latent attribution faults, OPEN by choice.** See the §7 index row. Recorded here
rather than fixed because both are behaviour changes and this session shipped a labelling fix and a
drawing fix; combining them would have made a rollback hard to reason about. Neither occurs in the 192
bills measured. **Also settled this session, and it removes an open backlog question rather than
adding one:** `ingest.min_confidence` (0.70) needs no tuning. Every Marg bill scores either 0.95+ (a
clinic ID is present) or 0.50 (it is not) — nothing in between, across seven days. The threshold was
imported from **OCR**, where the doubt is whether a scan was READ correctly; there is no OCR in this
path. It is a has-ID switch, and any value from 0.51 to 0.94 behaves identically. RULE: **a threshold
imported from another problem domain measures nothing here — measure the distribution before tuning
the knob.**

---

---

### §7.1 (continued) — S202 · F-184 *(reserved at the S201 close, appended at the S202 open, closed in the artefacts the same hour)*

**F-184 (S201, appended S202) — nothing numbered has ever owned the folder Phase 0 verifies.**

`deploy_kits/KB_canon_all/` is the only folder `verify_live_pins.py` will look in. It searches there
for a file hashing to the pin list's `source_md5`, and for the `CANONICAL_MANIFEST.md` beside it
pinning that same hash as CURRENT. Its `README_VERIFY.md` states the folder's contract in the
folder's own words: *"EVERY manifest-pinned canonical row, byte-authoritative in git"*, and
*"Everything else in this folder is listed. The inverse check is part of the close: files on disk =
rows listed + those two."*

**Three instances, one root.**

*(i) — reserved at S201.* The S200 close left the folder at Register v5.44 while pinning v5.45, so
its run could only ever return **AMBER (`register_not_in_repo`)**: every pinned file matching, the
source unprovable. The S201 run returned exactly that, and reading the checker rather than trusting
the word "GREEN" in a header is what found it.

*(ii) — found at the S202 open.* `MD5SUMS_ALL.txt` had not been rebuilt since the **S197 fold**.
Twenty-four files present in the folder were unlisted, including **every S198, S199, S200 and S201
canon document**, and the command exited with a WARNING on `CANONICAL_MANIFEST.md` — which **F-119
defines as a FAIL, not a footnote**. `KIT_ID.txt` read `KB_canon_S192close efcb8ac5…`, nine sessions
stale, and did not match the `MD5SUMS_ALL.txt` beside it (`cba2cbe5…`): **the one file whose only job
is to carry that hash disagreed with it.**

*(iii) — the one that matters.* **Twelve manifest-pinned canonical documents were not in the folder
at all**, living only inside per-close kits — `AUDITOR_SEED_v1` · `Clinic_Source_Data_Retention_Policy_v1`
· `S195_Medical_Watcher_LIVE_Reference` · `START_HERE_SESSION_194` · `195` · `196` ·
`S198_Purchase_Portal_Design_CONTRACT` · `Fault_Action_Register_v2_37` ·
`HANDOFF_RUNBOOK_2026-08-25_Session200close_v134` · `KB_History_Archive_v1_47_S200` ·
`START_HERE_SESSION_201` · `KB_Register_v5_21_S187`. So the one mechanical command the README calls
Phase 0 verification **had been checking a subset and reporting OK** — never wrong about what it
checked, and never saying what it was not checking.

**Why this is the F-107 family and not merely untidiness.** F-107 minted the observation that Phase 0
asks of each *listed* row *"do these bytes still match?"* and never asks of each *document in use*
*"are you listed?"* Here the same blindness moved one level out: the folder had a written completeness
contract, and no step asked whether the folder satisfied it. **Absence, not corruption, is what this
project has actually lost documents to (F-89, and the three S131 stumps).**

**Repaired at the S202 open**, in the order the fault itself teaches — every content change first,
every derived artefact last: the twelve documents filed (each verified against its manifest pin
*after* the copy, never assumed by filename — D188), then `MD5SUMS_ALL.txt` regenerated, then
`KIT_ID.txt` rebuilt from it.

**Not yet closed: the routine.** The repair is a state fix, and a state fix without a step is the
condition recurring. `END_OF_SESSION_PROMPT` **v8** owes an **A8b** that performs README_VERIFY's own
inverse check — files on disk versus rows listed versus manifest rows pinned — and refuses the close
on a mismatch. **RULE: a folder that carries an integrity contract needs a step that executes it. A
contract written in a README is a claim, not a check** — which is D188 applied to a promise instead
of a filename.

---

---

### §7.1 (continued) — S202 · F-185 · F-186 *(both found by measuring what a previous ruling had estimated)*

**F-185 (S202) — patient data in a public repository, and a sound ruling built on a wrong count.**

It was found by accident, which matters. A file was about to be copied from manojz INTO the repo, and
the standing rule is to scan for secrets and PHI before anything enters a public tree. The scan hit —
and then the scan was widened to the whole repo, because a hit in one file is a question about all of
them.

**F-96 (S181) recorded:** *"7 unmasked patient mobiles, ≥2 patient names and 1 clinic patient ID across
48 files."* **D320 ruled on exactly that evidence** that the repository may remain public, with the
binding corollary that no PHI-bearing artefact enters it.

**Measured at the S202 open: 133 distinct mobile-shaped numbers across roughly 190 files.** And the
count was not the worst of it. `plan-tool/test-data/patient_master.csv` and
`patient_diagnosis.csv` held **13 named patients with age, sex, full mobile number, presenting
complaint, diagnosis and comorbidities.** `recordings-archive/make_force_keys.py` held **38 real caller
numbers with call dates and times.** Three separate copies of `marg_report.py` carry patient names
paired with full mobiles and clinic IDs as selftest fixtures.

**Why F-96 missed it is the instructive part: F-96 examined the canonical DOCUMENT set.** It never
looked at code, and it never looked at a folder called `test-data`. The number it produced was true of
what it examined and false of the repository.

**Acted on the same hour, and only where action was safe.** The three orphan files were confirmed by
grep to be referenced by nothing in the codebase, then **MOVED — never deleted** — to
`D:\dr-manoj-git\_PHI_QUARANTINE_S202\`, with a README stating plainly that this stops them
travelling forward and does **not** remove them from past commits. **The live `marg_report.py` fixtures
were deliberately left alone:** scrubbing three repo copies while the live parser on manojz and the VPS
kept theirs would have manufactured precisely the record-vs-reality drift F-186 is about.

**The gate that was missing now exists** — `tools/phi_scan.py`, run by a double-click via
`PHI_SCAN.bat`, which **never prints a matched value**, because printing them is the thing it exists to
prevent. Its first run reports **271 files awaiting a first triage**; that number is the finding, not a
fault list, and an allowlist entry requires a stated reason.

**OPEN, and it is the owner's to close.** Only he can change the repository's visibility, and only he
can re-rule D320. **RULE: a ruling inherits the reliability of the facts it was given** — D172/D188
applied to a decision rather than to a filename, and the reason a decision deserves re-examination when
its evidence turns out to have been partial.

**F-186 (S202) — the live-pin discipline stops at the VPS, and something drifted in the gap.**

`margpull/signatures.json` on manojz hashed `3e9cbba0…` against a Register pin of `1b21f3bf…`. It had
changed during S201 and no record moved with it — **F-97's exact condition, on the one class of file
`verify_live_pins.py` structurally cannot reach.**

It was diffed rather than assumed, and the first diff was wrong: keying entries by (type, title_regex)
collapsed duplicate keys and reported "nothing added" when something had been. Redone by full-content
comparison: **6 entries pinned, 7 live, nothing removed.** Four report types gained an `end_marker` —
the row that proves an export finished — each carrying its own stamp, *"S201: every Marg report of this
type ends with this row, verified from a real sample."* One genuinely new `STOCK_CLOSING` layout variant
was added. One entry gained only a note explaining it has **no** end_marker *because no sample of that
variant exists to derive one from*, which is the pipeline reference's own rule being obeyed rather than
broken.

**The live file was strictly better than the record.** So the record was corrected FROM the box, per the
F-169 precedent, with second provenance being the S201 stamps inside the file itself; the repo mirror
was synced and the previous bytes kept as `.bak_S202_1b21f3bf`.

**The checker was not wrong — it was honest.** It classifies these rows BLIND and prints *"These are
blind spots, not passes. Nothing here was verified."* It said it could not see, and something had
indeed moved where it could not see. **This is the concrete case for B2**, and the second instance after
a two-builds-stale parser sat unnoticed on the medical PC.

---

---

### §7.1 (continued) — S202 CLOSE · F-187 … F-193, and the correction of F-185

**The session in one line: the pharmacy revenue feed went dark for eight hours and forty minutes and
nothing said so — and six of the nine findings raised around it are the assistant's own.**

**F-187 — a custody fact written where no query could reach it.** The words were there from 17-Aug, in
`cash_count.explanation` and the S186 close: *10,000 July advance + 20,000 August advance + 18,963 to
the owner*. Two of those three became entries. The third became prose. **A number in an explanation
column is not in the books**, and F-137 recorded that same shape before. What settled it was not
argument but a PHYSICAL COUNT — and the count also killed a plausible wrong theory first, which is
the part worth remembering: *20,003 with 3 written off* fitted the digits and was completely false.

**F-188 — the fix that broke the test, and the test was wrong.** Recording F-187 correctly pushed
Darpan's August advances over his ceiling, which is simply TRUE now, and three smoke checks that had
quietly assumed otherwise began posting negative amounts. **F-106's words, verbatim, eighteen sessions
later.** Reproduced offline on the unpatched app before a line changed.

**F-189, F-191, F-192 — three faces of one failure, and all ours.** A gate that matched the bare word
`OK` and would have accepted anything. A monitor wired to the success path so it could only ever
report success. A check that read a dead machine's last words as proof it was alive. **Each was built
to catch exactly the class of fault it then committed**, within hours. The never-fired witness in B2A
exists to name checks that never fire; B2B was then wired so it could never fire. That is not
carelessness so much as a warning about how ordinary this failure is: **the person building the
guard is not exempt from the thing the guard is for.**

**And the eleven-month instance is the one that matters most.** `E:\auto` on the medical PC has been
empty since October 2025. Automatic Marg backups were configured and have never run once, while a
human quietly filled the gap by hand every few days. Nobody was at fault; nothing looked wrong;
**there was simply never a moment at which anything asked whether the thing was producing output.**

**F-190 — the register that checked what was listed and never asked what was not.** `.gitattributes`
protected seven file classes and not the one that matters: `.md`, which is 192 of the 208 canonical
files. On a default Windows checkout every hash changes and Phase 0 fails on all of them at once.
**This has been latent since the repository was created**, invisible because one machine happens to
carry one setting. It is F-107's question — *what is NOT in the register?* — asked of file classes
instead of documents, and it would have surfaced on exactly the day the cold kit was needed.

**F-193 — three messages that named innocent causes.** A pull that blamed a switched-off PC and a
disconnected tunnel while both were demonstrably fine. Windows warning about *malicious devices* for
a credential. Marg demanding a **re-install of a live pharmacy ERP** because it was started from the
wrong folder. Roughly an hour went into the first of those. An error message is a diagnosis, and a
diagnosis that lists only what it cannot distinguish is worse than silence, because silence does not
send anyone anywhere.

**F-185 — corrected, and the correction matters more than the finding.** The assistant told the owner
that thirteen named patients and their diagnoses were exposed in a public repository, urged him to
act, and pressed when he pushed back. **It was false.** The protection he had built years earlier —
`.gitignore`, `*.csv` — had been working perfectly the whole time. The scanner asked the filesystem
what existed instead of asking git what was published, and reported files that git was deliberately
holding back. **RULE: to make a claim about what is public, ask the thing that publishes.** The
scanner now refuses to run at all if it cannot reach git, rather than degrading to the wrong question.

## §7.1 (continued) — S203 · F-194 … F-206 *(raised and appended the session they were found; the AF-1 strike proposed at this close and refused on measurement)*

> **Why this section reads as a chain.** Three of these findings were not discovered
> independently. **Each became visible only because the one before it had been fixed**, in a
> single evening, and the order matters more than the individual defects:
>
> **18:38 — F-197 fixed.** The pull got a log. Until that moment the leg was dark: `PULL_HIDDEN.vbs`
> had discarded stdout every ten minutes for a session and a half.
> **18:44 — F-194 became legible.** The first log ever kept ended
> `pipeline_status: post failed (HTTP Error 401)`. **That line had printed on every pull since
> S202** and been thrown away every time.
> **18:51 — F-194 root-caused, and F-195 with it.** The 401 came from `_gate()`, not from the
> route. `/finance/api/pipeline-status` had been added at S202 and never added to the gate's
> three-path exemption. **B2 — the pipeline heartbeat, the whole point of two kits at S202 — had
> never once reported.**
>
> There is no version of this evening in which F-194 is found without F-197 being fixed first.
> **The first fix in a dark leg is a log, not a theory** — and that is the transferable lesson,
> not the 401.

### The proof standard applied, and where it was not met

**F-194 was proven twice and in both directions.** A POST from the VPS carrying the server's own
`FINANCE_MARG_TOKEN` returned **401 `not_signed_in`** against the unfixed app and **HTTP 200
`{"ok":true,"received_at":"2026-08-26T18:52:00"}`** against the fixed one. That is a proof about
`curl`. So it was then proven from the **real caller**: three consecutive
`pipeline_status: 200 (token from medical PC (live))` lines in the pull's own console log,
**including the scheduled runs at 19:10 and 19:17** — the path a human never touches.

**F-198 met the same standard.** Its seven new checks were run against the **unfixed**
`marg_router.py` before the fix existed: **five go RED**, and the two that pass were already true.
**F-198's sibling in `pipeline_status.py` likewise** — six checks against the unpatched parser make
**check 10 FAIL**. Reverse application on every file in this session returned **exactly** to its
live pin.

**F-195 is where the standard was not met, and it is ours.** The two smoke checks written at S203
to close the hole F-194 came through **do not bite**: reverting the gate still gives **721/721**.
They were not run against the broken state before being trusted. They are recorded here as
green-and-meaningless rather than left in the suite looking like coverage, which is the only useful
thing to do with a check that cannot go red. Counts this session: `marg_router.py` selftest
**14 → 21 (+7)**, `pipeline_status.py` selftest **15 → 21 (+6)**, VPS smoke **719 → 721 (+2)** —
every projection written down before measuring, every one landed, and the +2 nonetheless proving
nothing.

### The medical PC, seen for the first time

`medical_census.py` S203.6 read the machine at **13:04** and produced the **first live pins ever
taken on it** (`deploy_kits/S203_CENSUS_BACKUP/S203_MEDICAL_PC_PINS.md`, eight files). **Drift
there had been undetectable by construction from the day it was set up:** `verify_live_pins.py`
runs on the VPS and cannot reach it, the Tailscale share is read-only and D:-only, and the manojz
mirror never purges (**F-199**). Everything ever said about that machine from the mirror was a
statement about its history.

**F-199 and F-206 are the same fault at two removes.** The mirror showed `GUARD_AND_SEND.bat` on a
machine that does not have it; a record said AF-1 was armed against `GUARD_AND_SEND.bat`; and the
close proposed to strike AF-1 because the file is gone. **Three correct-looking steps and a wrong
answer**, because none of them asked where the *mechanism* was. It is in `SEND_TO_CLINIC.bat`,
live, right now, at `e19a8a777ac22fe75a242f1eb9762185`.

### AF-1 — the strike, struck

**PROPOSED AT THIS CLOSE, AND PRESERVED HERE STRUCK RATHER THAN DELETED (F-23):**

> ~~*Strike AF-1: it is armed against `GUARD_AND_SEND.bat`, which the medical PC's own file listing
> proves is not on that machine. The fallback D347 protects is `SEND_TO_CLINIC.bat`, which is
> self-contained.*~~

**REFUSED.** The evidence, read from the current bytes rather than from any record:

- `GUARD_AND_SEND.bat` is **88 lines**; it invokes `guard_and_send.py` and then hands off to the
  sender. A search of it for `curl`, `last_response`, `sent_hashes`, `ACCEPTED-FOR-REVIEW` and
  `http_code` returns **nothing**. **AF-1's mechanism was never in that file**, so its absence from
  the machine says nothing about AF-1.
- AF-1 was recorded against **`SEND_TO_CLINIC.bat`, kit `S187_M1a`**. The live file is
  **`e19a8a777ac22fe75a242f1eb9762185`** — one of the eight pins taken at 13:04, i.e. present and
  current on the machine.
- In those bytes: `curl -s -m 90 -o "%RESP%" -w "%%{http_code}" …` writes the reply to
  `last_response.txt`, and **there is no `del` of `%RESP%` before it**. `curl` does not touch its
  output file when the connection fails, so on any network failure the file still holds the
  **previous** run's reply.
- The success decision is `findstr /c:"ACCEPTED-FOR-REVIEW" "%RESP%"`. **`%HTTP%` is captured into
  `last_http.txt` and read — and then consulted only in the REFUSED message further down.** It
  never gates the ACCEPTED branch.
- That branch runs `echo %HASH%>> "%HASHES%"`, and the skip test at the head of the routine
  (`findstr /i /c:"%HASH%" "%HASHES%"`) then refuses to resend that exact report **for ever**.

**So `SEND_TO_CLINIC.bat` is self-contained — it posts directly and calls neither the guard nor the
parser — and AF-1 is live inside it.** Both halves are true at once, and the strike confused them.
A day's pharmacy staging can still be reported ACCEPTED, logged ACCEPTED, and permanently
blacklisted, behind a success message, on nothing worse than a dropped connection. The cure —
deleting one line from `sent_hashes.txt` — remains written nowhere the person at the machine would
find it. **AF-1 stays armed; F-206 records why it was nearly not.**

### What was measured at this close rather than read

The two source documents were hash-verified before either was touched
(`KB_History_Archive_v1_49_S202.md` `06c6670a8a1155959e4f0961ad58e7c5`,
`Fault_Action_Register_v2_41.md` `4883e3bdf08cba92da7597448e00f2da`), and every live pin quoted in
these thirteen rows was re-hashed on disk rather than copied from the fact sheet. Two things did
not check out and are recorded rather than smoothed: **`S203_CENSUS_BACKUP` carries no `SUMS.md5`**,
against the close's claim that every kit folder carries a verified one; and the seven files in
`S203_MARG_CANON` that its `SUMS.md5` does not list were each inspected and are
**`SUMS.md5.before_*` backups of the sums file itself**, not unlisted content — so the folder's
**67** is right and its `md5sum -c` exit 0 means what it says.
## §7.1 (continued) — S205 · F-213 … F-217 *(raised and appended the session they were found; every one by measuring a record against the machine it describes)*

| # | status | finding |
|---|---|---|
| **F-213** | **S205 · OPEN** | **The tool the close-out depends on is outside the record.** `/root/deploy/gen_live_pins.py` is **untracked, unpinned and in no Register row** — the instrument that measures the estate is itself unmeasured. **Confirmed live at S205** by the owner's own `verify_live_pins.py` run, which lists it among its 85 untracked files. Nothing is lost today: a v1.2 copy sits at `deploy_kits/S187_V1a/` and was proven at S204 to reproduce the S203 pin list byte-for-byte. **What is missing is the record** — nothing says the live copy and that repo copy are the same file, and nothing would notice if they stopped being. **Fix:** pin it, give it a Register row, and have the close assert that the live copy still reproduces the repo copy's output. Kin of F-209 and F-184. |
| **F-214** | **S205 · OPEN (partly fixed)** | **`.gitattributes` states a reason that is FALSE, and the pull batch can never match its own kit.** Line 48-49 justifies pinning `*.bat` to CRLF with *"the live PULL_FROM_MEDICAL.bat is CRLF"*. **Measured: 52 CRLF and 228 bare LF — mixed.** Three copies therefore disagree in three directions: running on manojz `cfb8b13d…` (mixed) · the committed blob (all LF) · what a **fresh clone** produces under the `eol=crlf` rule (all CRLF, a third md5). So `deploy_kits/S203_R2/`, which exists so the pull batch can be RESTORED, restores as a different file from the one running. It has never bitten only because git applies `eol=` on checkout and the file has not been checked out since S202 — **the rule is declared and has never been applied**, on a machine whose `core.autocrlf=false` is the same single unrecorded setting the `.gitattributes` comment itself names as the disaster-recovery hazard. **Partly fixed:** the S205 `PULL_FROM_MEDICAL.bat` is CRLF throughout, so live and a fresh clone agree for the first time; `SEND_TO_CLINIC.bat` was **also LF-only** and is likewise fixed. **STILL OWED:** correct the false sentence, and ask the same question of every other `.bat`/`.cmd`/`.vbs` on both PCs. **The shape: a rule written from a belief about a file nobody measured** — F-208's error applied to a file attribute. |
| **F-215** | **S205 · FIXED in the artefacts · STRUCTURALLY OPEN** | **THE REINSTALL KIT RESTORES THE FAULTS IT WAS CAPTURED TO SURVIVE.** `deploy_kits/S203_LIVE_TOOLS/manojz/` was taken at **12:42 on 26-Aug**; the three S203 repair kits landed at **12:53, 13:04 and 14:47** — *after* it — and nothing re-captured at that close or at S204. **Three of its ten files held the PRE-FIX bytes**, each byte-identical to the `.bak_S203_R*` backup still on manojz: `PULL_FROM_MEDICAL.bat` `92f03999…` (**the version that writes `-- ok` UNCONDITIONALLY — F-196**) · `marg_router.py` `bbc50f91…` (pre-`S203_R1`) · `pipeline_status.py` `51cf10c9…` (pre-`S203_R3`). **A rebuild from its only kit would have restored the exact fault that ran the feed dark for 8h40m while reporting itself healthy every ten minutes.** **And `md5sum -c` on it exits 0** — because it hashes the kit against **itself**. *A kit verified against its own copy proves nothing about whether it matches what is running.* **F-209's mirror image**: there a hash was green and the bytes did not exist; here the bytes exist, they are the WRONG bytes, and the hash is green for that too. It was also **missing nine files**, including **`PULL_HIDDEN.vbs`** — the file the scheduled task actually launches; a rebuild would have restored the pull and not the thing that runs it. **FIXED:** `deploy_kits/S205_LIVE_TOOLS/` — 24 files each verified **against its live source**, 0 drift, + both reinstall documents. **STRUCTURALLY OPEN:** nothing numbered re-captures (same omission as F-184 and F-200) — **now A11 of `END_OF_SESSION_PROMPT_v8`** — and `md5sum -c` on a kit must never again be reported as evidence the kit is current. |
| **F-216** | **S205 · OPEN** | **THE 85 FILES THE RECORD NEVER MENTIONED — F-209 an order of magnitude larger.** `verify_live_pins.py` has printed, under every run, *"Either add it to the Register, or add an IGNORE line saying why it does not belong."* **No numbered step owns that decision, so in 85 cases it has never been made** (F-184's shape). F-209 asked whether the **pinned** files exist elsewhere and found four that did not; nobody had asked it of the ones the record does not mention. **Measured at S205, by md5, on both sides: 85 untracked VPS files against 2,030 repo files → 38 identical, 47 EXIST ONLY ON THE VPS.** Of those 47, **24 have no file of that name anywhere in the repo**: `portal_config.py` · `att_config.py` · `watchdog_live_copy.py` · `patch_switcher.py` · five `attlistener_phase*.py` · **and the entire finance deployment toolchain, 12 files** — `install_finance_S179.sh`, `post_install_finance.sh` (named in `finance_app.py`'s own source as the thing that **writes the real usernames into `unit_role`**, i.e. who may approve money), `add_finance_vhost.sh` and nine more. `S204_C1` captured the money application's **bytes**; it did not capture **how it was installed or who it was configured to trust**. Also `wa_receiver.py` runs **16,915** bytes against the repo's **14,035** — the live receiver has moved on and nothing stored the move. **23 are genuinely disposable** (6 `*_BACKUP_*`, 12 generated HTML renders, 5 one-off diagnostics) **and should get an IGNORE line each, with its reason** — that is how 85 stops being a number nobody reads. **Remediation is NOT "push them to git": F-185 is open and the repo is PUBLIC.** Configs and a username-writing installer go to a **private capture kit**, gated per file. **A correction recorded rather than quietly fixed:** `/root/wa/staff_ledger.py` (138,215 b) was first read as the live ledger existing in one place; every repo version is 142–242 KB and this one matches the pre-SSO backup beside it — **a stale copy in `/root/wa/`**, not the live app. *A size and a path are not provenance.* |
| **F-217** | **S205 · FIXED · pre-existing, found by running it where it runs** | **A SELFTEST THAT CAN ONLY PASS WHERE THE THING IT TESTS CANNOT HAPPEN.** `pipeline_status.py`'s check *"a missing heartbeat path falls back rather than reporting a silent green"* asserted `pick_heartbeat(<missing>) in (None, hb)` — **a RESULT, which depends on which heartbeat files exist on the machine running the test.** Offline none of the Windows paths resolve, so it returned `None` and went green; **on manojz — the only machine this file ever runs on — a real heartbeat sits at `DEF_HEARTBEATS[2]`, so it returned that: correct behaviour, failed assertion.** The line is **verbatim in the live S203_R3 file** (`0b3dd968…`), so the live selftest has never passed on manojz and nobody knew, because it was only ever run offline. **FIXED:** `pick_heartbeat` now takes its candidate list so a test can be deterministic, and the one machine-dependent assertion became four assertions of the PROPERTY — 45 checks, green on any machine. **And within the hour of writing the rule, the assistant nearly repeated it**: `_dest_ok` in `medical_agent` S205.1 first used `os.path.abspath`, correct on the medical PC and meaningless anywhere it could be tested; rewritten to resolve paths by hand. **The family: F-195 (a test), F-215 (a kit's `md5sum -c`), F-216 (a pin check green over an incomplete list), F-217 (a selftest) — four instances in one session of *a check that passes for a reason other than the one it names*.** |

---

### §7.2 — S209 INDEX ADDENDUM (30-Aug-2026) · the fork ratified, and six new faults

**D353 RATIFIED THE F-SERIES FORK** on the owner's "YES PROCEED", applying the S197 rule
verbatim: *every number already in circulation keeps its meaning; unnumbered findings are minted
into the gaps; numbering is therefore not chronological, and that is recorded rather than
silently reordered.* Leaving findings recorded elsewhere but never applied here **is the F-108
condition by definition**.

**The fork was measured, not recalled.** This register's §7 index runs to **F-217**; the
ratified set ends at **F-212**. The candidates form four cohorts, each owned by the session that
raised it: **F-218…F-222** (S205/S206 housekeeping) · **F-223…F-231** (S207, the Marg
reconciliation) · **F-232…F-236** (S207, the no-mint session) · **F-237…F-239** (S208).
**F-220, F-221, F-222, F-227, F-231 and F-236 are ratified as NUMBERS but their text is not
transcribed here** — it exists verbatim in the S206/S207 documents, and writing a register row
from a number recognised but a finding not read is **F-135's shape**. Transcription is owed.

**STRUCTURAL NOTE, recorded not silent:** these rows are appended as §7.2 rather than inserted
into the §7 index mid-file. The file is 383 KB; a mid-file insert re-types content that no one
has read, which is **F-23's shape** (sixteen lines silently dropped by a document claiming to
carry a prior version forward). Appending is provable; inserting is not.

| # | state | the finding |
|---|---|---|
| **F-241** | **S209 · CLOSED same session** | **A PAGE SHIPPED WITH A SYNTAX ERROR AND EVERY GATE WENT GREEN.** `finance_approvals.html` carried `h+='... the same patient's own earlier sale bill ...';` — an English possessive inside a single-quoted JS string. A syntax error anywhere in a `<script>` block stops the WHOLE block: **every section of the owner's money console sat on "loading" for a day.** The kit's `SUMS.md5` passed (the file WAS delivered intact), the finance smoke suite passed (721 checks — it tests routes and payloads, not pages), and the S208 close recorded the console live and verified by hash. **Nothing in the toolchain has ever parsed a page's JavaScript. "Intact" is not "valid".** Fixed on the box, hash-proved `da82366c…`; gate built (`S209_JSGATE`, `node --check`, three exit codes so a gate that cannot run never looks green — F-119). Sweep: 42 script blocks across 36 pages, **exactly one failure — this one.** **RULE: a delivered file is not a working file; if a page carries code, parse it.** |
| **F-242** | **S209 · OPEN** | **THE LOGIN TRAP: `_authed()` on the door, identity inside.** `/portal/login` redirects to `/portal` when `_authed()` is true, and `_authed()` is satisfied by the legacy trusted-device cookie ALONE; `/portal` then applies F-98 (*"a trusted DEVICE is not an identity"*) and redirects back. **A browser holding the device cookie with no valid SSO token loops forever, with no exit** — the cookie is HttpOnly so no page can clear it, and `/portal/logout` is 404. The F-98 fix was applied to `home()` and never to `login()`. Caught the ASSISTANT's browser (signed in at S208, invalidated by the 10:56 epoch bump) and was briefly mis-reported to the owner as his own fault. **RULE: a fix applied to one of two doors is not applied.** |
| **F-243** | **S209 · OPEN** | **`clinic_users.json` HAS NO BACKUP.** Census found exactly one copy — `/root/portal/clinic_users.json`, 3,187 bytes — and no `.bak` anywhere on the box. **That single file is all twelve logins.** Nothing in the close routine copies it and it is not in the pin list. F-209's shape (*a hash is not a backup*) on the identity store. |
| **F-244** | **S209 · OPEN — the only red kit gate left** | **`S195_A123` HOLDS THREE HASHES AND THE RECORD KNOWS NONE OF THEM.** Its SUMS row demands `6617ec6f…`; the file present is `e1791014…`; live is `8427c82e…`. **Neither of the first two appears anywhere in the KB Register or this Archive.** So it is not a kit lagging behind live — it is a kit whose contents no longer match what it shipped with, citing a hash nothing ever pinned. It is `finance_app.py`. Left RED deliberately with `DO_NOT_INSTALL_S209.md` beside it: **making the gate green would certify bytes nobody can account for.** |
| **F-245** | **S209 · CLOSED same session** | **THE OWNER-ONLY TRANSFER CONTROL HAD NO SCREEN.** `S208_LEDGER3` shipped `api/ledger-check` and `api/transfer` and the message *"Record it as an owner transfer below"* — and **the word "below" referred to a control that was never built.** Exactly one `darpan_corrections.html` exists in the repository (3,157 bytes) and it references neither route. **The owner was directed to this control for three days; it existed on no page.** **F-161 exactly** — *a capability without its wire is a claim; grep for the CONSUMER, not the definition* — second instance of the class in one day. Built, gated and installed as `S209_TRANSFER_UI`. |
| **F-246** | **S209 · CLOSED page-side; server wording kitted** | **A WARNING WHOSE PRESCRIBED REMEDY CANNOT SATISFY IT.** `api_ledger_check` counts `cash_movement` rows; `api_transfer` writes `cash_custody_event`. So the owner followed the instruction exactly, and the page went on saying *"the transfer-out was never saved"* — which reads, to the man who just did the work, as "it did not save". **Owner's correction, recorded:** an early rewrite said *"an owner transfer is not a day-ledger movement"*; he rejected it — **it IS a cash movement in real life**, drawer to Dr Bhawna. The true statement is narrower: no row was written into that day's ledger. **RULE: a message that names a remedy must be satisfiable by that remedy.** |

---

**END OF FAULT → ACTION REGISTER v2.45 — §7, §7.1, §7.2 and the CHANGELOG are the last sections. If any of the three is absent, this file is truncated and must not be used as canonical.**

---

# MINTED AT THE S212 CLOSE — F-247 … F-264

**F-247 … F-258 were ruled by the owner on 30-Aug-2026** (`S211_CANDIDATE_RULINGS.md`, *"All twelve
accepted… they mint as F-247 … F-258 at the session close, in the order a–l"*) and were OWED from
the partial S211 close. **F-259 … F-264 are found and measured at S212.** All fixes described were
already made; numbering does not repair anything, it remembers it.

## The S211 twelve

| # | fault | the lesson |
|---|---|---|
| **F-247** | **A cash balance can go negative.** `counter` and `drawer` in `v_cash_custody_balance` are pure deltas; confirmed live 30-Aug at `counter −1,56,235`, `drawer −42,093`. Owner: *"against accounting, so confusing."* | **A physically impossible number should be refused by the code, not displayed.** |
| **F-248** | **The money card rendered twice and the walkthrough passed anyway** — it ran against the wrong sample data. *(assistant's own)* | **A test can be green and be looking at something other than what the owner sees.** |
| **F-249** | **A day wore a "not filed" badge after it had been filed** — a snapshot taken at push time presented as the present moment. | **An old snapshot presented as "now" is a lie, even when the snapshot was honest.** |
| **F-250** | **Apply failed on `database is locked`** — the second writer gave up instantly. Fixed with a 30-second patience wrapper. **Carries a build item:** say "applying", then a plain popup either way, in the server's own words. | A concurrent writer must wait, not surrender. |
| **F-251** | **Two copies of `darpan_app.py` drifted** — `S208_CONSOLE` vs `S208_LEDGER3`. **RULED: retire the stray**; CONSOLE is the live lineage. | Two live copies of one file is a decision waiting to go wrong. |
| **F-252** | **The sweep assumed Node on the VPS.** Its own output reported the absence and it was fixed the same hour — the system working correctly. | A detector that degrades honestly is doing its job. |
| **F-253** | **`__pycache__` left behind; the publish gate refused** — the same mistake as S207, a selftest run without `python -B`. *(assistant's own)* | **A gate refusing is not a nuisance; repeating the same mistake is.** |
| **F-254** | **The Remove button could never have worked, not once.** The CHECK constraint admits pending/applied/rejected/superseded; the button wrote `dismissed`. **Every press failed from the hour it was written.** The owner pressed it four times over two days. | **Code that writes to a store must be tested against that store, not merely read.** |
| **F-255** | **The test for that button never pressed the button** — five green ticks for installed, compiled, idempotent, filter-present, and it never called it against a database. *(assistant's own)* | **A test that measures the wrong thing is worse than no test, because it ends the search.** |
| **F-256** | **The screen said "network" for every failure**, because it could not read an error page and guessed. Cost the owner two days and a browser cleared for nothing — and the same fault sat on the **Approve** button he presses daily. *(assistant's own)* | **A screen must report what the server said, never what it assumes.** |
| **F-257** | **A kit was recorded live and was not installed.** Nine kits noted at S210; the installer applied five, and `S210_DBPATIENCE` was not among them. Nothing could tell built from installed until `tools/live_census.py`. | **"Installed" must be a measurement, not a note in a document.** |
| **F-258** | **A warning outlived the problem it warned about.** The manifest said §S205 had never been written; it had been written at the very next close, five sessions earlier. Seven documents sat blocked on a decision already made. | **A warning is a claim with a date on it. Nothing retires it but a fresh measurement.** |

## The S212 six — found and measured this session

| # | fault | the lesson |
|---|---|---|
| **F-259** | **THE REINSTALL KIT CANNOT RESTORE THE MEDICAL PC.** `S205_LIVE_TOOLS/medical/SEND_TO_CLINIC.bat` is **v3**, which decides success from the reply body alone and never reads the HTTP code. On a timeout the previous body remains on disk, `findstr` finds `ACCEPTED-FOR-REVIEW`, and the report's md5 enters `sent_hashes.txt` — **blacklisting a real sale report permanently.** Live is v4 (the AF-1/F-206 fix, applied 27-Aug 01:12). Also stale: `medical_agent.py` S203.3 vs S205.1 live; `GUARD_AND_SEND.bat` v1 vs v2 — the icon reception uses. **Four files are in no kit at all**, including `marg_macro_calib.txt`, screen coordinates that cannot be recreated. `REINSTALL_MEDICAL.md` §8 still describes AF-1 as unfixed, so a rebuild would make its own documentation true again. **The kit's MANIFEST predicted it:** *"the moment the S205 kits are installed, two of these 24 files are stale."* They were installed that night; five sessions passed. Repair staged as `S212_LIVE_TOOLS`, verified against live. | **A gate that hashes a kit against itself proves it is intact, never that it matches the machine.** F-215, one generation on. |
| **F-260** | **`signatures.json` in the reinstall kit holds 7 signatures against 8 live** — the missing one is `PURCHASE_ITEMWISE`, installed at S205 as *"the biggest single unlock — five months of item-level purchase data quarantined."* A rebuild would run, **pass all six of its own proof checks**, and silently route every item-wise purchase report to `_UNKNOWN`. `xlrd\` is required by `REINSTALL_MANOJZ.md` §3 and exists nowhere in git. | **A proof check that cannot see the thing that changed is not a proof.** |
| **F-261** | **`finance.db` has no offsite backup.** The nightly Drive job carries twelve follow-up-tracker CSVs; the database holding 17,146 item lines, the staging table, the five stock-ledger tables and the 7,816-row patient spine is in none of them. Searched the whole Drive: the only other `-db.gz` is a WordPress set, and `MargBackups` is Marg's own. | **The thing most worth backing up is the one nobody remembers to add.** |
| **F-262** | **MARG'S TWO EXPIRY REPORTS ARE INDISTINGUISHABLE AND ONE HID A REAL ITEM.** ALREADY-EXPIRED and NEAR-EXPIRY carry byte-identical headers, so both archive as `STOCK_EXPIRY_DEFAULT`. Three near-expiry exports landing 28-Aug aged out the 23-Aug expired list, and **`VINBACTUM DS` — 25 vials, expired 2/2025, the shop's entire expired exposure, ruled for write-off under R6 — silently left `current`.** Confirmed by reading all five 2026-08 files: it appears in exactly one. Owner confirmed from Marg that the item is genuinely still held. Fixed by classifying the family **from content**. Second instance of F-235. | **When two things share a name, decide between them by what is inside, never by which arrived last.** |
| **F-263** | **THE ARCHIVE DOUBLE-COUNTS BY DESIGN.** `marg_router.py:394` skips a file only when its content md5 has been seen; two different exports of overlapping periods are both kept and both look valid. The sale archive already carries three such pairs. **Under the agreed cadence — month-to-date on every Amir visit — every export contains the previous one.** Specified at S206 Phase 0 (*"without that rule the archive double-counts silently"*) and never built; the S212 stock walk over-counted on its first run for exactly this reason. Built as `S212_SUPERSEDE`. | **Deduplication by content answers "is this the same file", never "is this the same period".** |
| **F-264** | **ONE RULE, SEVEN IMPLEMENTATIONS.** The Marg pack rule is written in `units.py:52`, `packmap.py:38`, `marg_stock.py:33`, `build_report.py:14`, `build_stock_check.py:22` (which declares the duplication in its own docstring), `finance_item_anomaly.py:91` and `finance_money.py:32` — four of them disagreeing on edge cases. **S206 already held the money model** (`build_report.py:72`, and `load_fy.py:87` renames `amount_p` → `rate_p` at ingest) and S211 re-derived it over 374 bills. Measured: none of the disagreements can fire on real data — every pack has outer = 1 and no `N*M.5` pack exists. Three PC kits were additionally found hard-coded to the assistant's sandbox mount and unable to run on manojz at all. | **Before deriving a rule, search the repository for it.** Six sessions wrote this rule rather than found it. |

**Next free: F-265.**

**Carried, unchanged:** **F-244** (`S195_A123`, the one deliberately red kit gate) still awaits a
ruling.

---
*Minted at the S212 close, 31-Aug-2026. F-247–F-258 ruled by the owner 30-Aug; F-259–F-264 measured
at S212. b, g, i and j of the S211 set (F-248, F-253, F-255, F-256) are the assistant's own mistakes
and are marked so rather than folded in among the rest — as are F-259's five-session blind spot and
F-264's seventh copy.*

---

# MINTED AT THE S213 CLOSE — F-265 … F-268 · and D357

**All four found and measured at S213, the session that put the first four items of the decided
order live.** F-265 was the assistant's own wrong assumption, caught by its own preflight before
any data moved; the other three were found by refusals and by running walks on the real machines.

| code | finding | the rule it leaves behind |
|---|---|---|
| **F-265** | **SERVICE ACCOUNTS HAVE ZERO DRIVE QUOTA.** The F-261 backup's v1 design (the service account CREATES a file per night) was refused live: HTTP 403 *"Service Accounts do not have storage quota. Leverage shared drives … or use OAuth delegation."* The early signature was visible one step before: the About endpoint reports `quota used 0 of 0`. v2 UPDATES two owner-owned slot files instead — content updates bill the OWNER's quota, so a zero-quota SA can still ship. The assistant's own: v1 assumed SA storage that no longer exists; contained by the preflight's test-write, which is why preflights exist. | **A service account can no longer own bytes on Drive — it can only fill files a person owns. Every SA-to-Drive design starts from update-in-place.** |
| **F-266** | **A PIN'S IDENTITY NOTE IS NOT THE FILE.** `/root/finance/finance_app.py`'s pin `e9b64d97…` carried the identity "S208 pin + four S210 patches" — and the S213 r2 patch's guard found the S211 day-gaps route (MARK `S211 (day gaps api)`) ALREADY LIVE at line 3050. The r1 install happened after the pin was captured and was never recorded; the register said one thing, the box another. The patch grew a byte-anchored UPGRADE path (r1's exact jsonify → r2) and applied clean; a drifted r1 would have refused. | **The S212 rule's sibling: a `KIT_ID.txt` is not evidence of what is running, and neither is a pin's identity note. The grep is.** |
| **F-267** | **TWO STALE MANIFEST PINS, one of them unprovable.** (i) `LOCAL_KB_EXTENSION_PLAYBOOK`: the S207-close pin `3f3cd28e…` exists NOWHERE — ClaudeCowork, the SSD copy and the inside of the S207 mirror zip all checked; the file postdates that zip by ~45 min, so the pin was taken on bytes that changed before any copy froze. Both stores identical at `d38fbc4a…`, every element the row names present; ruled LOST-SUPERSEDED on the `START_HERE_PROMPT_v6` precedent, row re-pinned. (ii) `MARG_WALL_CARD`: the row kept the S203 hash through its own "UPDATED S205" note while the manifest's census line and BOTH kit copies agreed on `dd018563…` — the row was stale, not the file. The F-97/F-123 family. | **A pin must be frozen into a mirror the same hour it is taken — a mirror that predates the pin cannot prove it. And a row's own tier cell saying "UPDATED" is a claim; the hash cell is the record.** |
| **F-268** | **SQLITE MUST NEVER WRITE INSIDE THE MOUNTED REPO.** The S213_STOCK_SCREEN walk passed 27/27 in the sandbox and failed its FIRST call on manojz: sqlite locking does not survive the device mount, and the scratch files it left could not even be deleted there (the no-delete rule). The walk's database moved to a temp dir outside the mount; the scratch went to `D:\dr-manoj-git\_to_delete_S213\` with `WHY_SAFE.txt`. Found only by running the walk on the real machine — the sandbox could never have shown it. | **Anything that writes a database writes it OUTSIDE `mnt\`. And a walk is not finished until it has run on the machine it claims to prove.** |

**D357 (owner, 31-Aug, after the returns-card live walk):** *"all ok, needs some display setup and
further analytics etc, and send to darpan, etc — park it for later."* The returns card's display
polish (its own card, not a corner of the Marg card), further analytics, and serving it to Darpan
are **PARKED on the owner's word** — picked up when he says, not scheduled.

**Next free: F-269 · D358.**

---
*Minted at the S213 close, 31-Aug-2026. F-265 is the assistant's own assumption, refused by the
live box and contained by its own preflight; F-266–F-268 were found by a guard's refusal, a Phase-0
sweep, and a walk run where the code actually lives.*


---

# MINTED AT THE S219 OPEN — THE S217/218 FOLD — F-269 … F-275

**The seven roots the marathon named in `S218_BUILD_BRIEF` §roots, minted here as the deferred close
owed (S211 precedent). Every one was found by the money being wrong on a surface the owner looks at
every day, or by the owner himself (F-273). Two are the assistant's own: F-269 (a test that wrote
into the live store for eighteen sessions) and F-271 (a column shipped ahead of the migration that
defines it).** Authored from Archive §S217/218 and `S217_UPI_INCIDENT_FINDINGS`, never from memory.

| code | finding | the rule it leaves behind |
|---|---|---|
| **F-269** | **THE SMOKE SUITE WROTE ITS FIXTURES INTO THE LIVE STORE.** `/finance/api/upi-statement` runs the smoke against a throwaway DB but stores every posted file into the LIVE `upi_statements/` dir — since S179. 150 fixture files accumulated unseen; on 30-Aug a backfill replayed the store and nine `RRN1`/₹999 fixtures overwrote the real rows for nine August days. Nothing red anywhere: the day totals in `upi_statement` were intact, so every health check that read totals passed. Repaired by `S217_UPI_REPAIR` (quarantine 150 → backfill 183 real → delete RRN1 → reconcile: all days agree). **The route patch that stops the store is still OWED.** The assistant's own. | **A test's fixtures never share a store with live data — not a table, not a directory, not a bucket. A smoke run must leave zero bytes where production reads.** |
| **F-270** | **A GATE THAT QUIETLY DIVERTS IS WORSE THAN ONE THAT REFUSES LOUDLY.** The 0.70 identity-confidence gate parked ~118 credit notes and every name-only sale in the review queue for five months while every surface said "no patient". The queue existed and nobody was made to look at it; the money it held was invisible to the drawer, the returns card and the month close alike. D355's lookup replaced the gate; `backfill_lookup_s218.py` booked 93 rows (49 master, 44 named-stub), queue 93 → 0. | **Anything a gate holds back must shout on the owner's surface with a count and an age. A silent queue is a hidden ledger.** |
| **F-271** | **A COLUMN SHIPPED AHEAD OF ITS MIGRATION.** `finance_daily_gaps.py:217` selected `patient_ref.mobile`, a column D356 was to create — and D356 had never been deployed. The line executes only on a day with an UNMATCHED bill, so four green offline days proved nothing (the S216 lesson again) and the first real unmatched day 500'd the CounterGaps card. Reproduced offline byte-for-byte before `S217_DAYGAPS_FIX` touched the box. The assistant's own. | **Code that reads a column proves the column exists on the box it ships to — in its own preflight, not in a comment. A rare branch is walked on purpose before it is walked by a patient.** |
| **F-272** | **A STATEMENT THAT ARRIVED AFTER THE FILING WAS NEVER RE-COMPARED.** The save-time reconcile fired when a day was filed; a bank statement landing later (the ICICI mail slipping from ~08:40 to ~11:15, past the single 09:30 push) met no compare at all. 28-Aug was filed with UPI ₹999 — exactly the fixture — against bank ₹6,687, and the drawer read inflated by ₹5,688 for three days with nothing shouting. `finance_heal.py` now re-runs `upi_vs_statement` at every feed arrival; GAS v3 pushes hourly and shouts at 15:00 if no statement mail came. | **A comparison between two feeds runs when EITHER feed moves, not when the first one did. The owner's law: feeds land late and out of order; a record written in the gap must be re-checked when reality arrives.** |
| **F-273** | **CORROBORATION AGAINST A STUB POOL IS NOT CORROBORATION.** CN00184: a return attributed to WALK-IN carried the verdict NEVER-BOUGHT, because the check searched WALK-IN's 1,956 bills and found no matching purchase — a pool that would "corroborate" anything and therefore proves nothing. Owner-caught, 02-Sep. The verdict had been rendered on Darpan's sheet as a real finding. Ruled: a stub-attributed row never carries a corroboration verdict; it shows "identity needed" and goes to the Darpan sheet; only master-matched REAL flags auto-escalate. Build owed (M7 / S219_QUEUE #2). | **Every verdict has an identity precondition. If the row's patient is a stub, the verdict is "identity needed" — never a finding about money.** |
| **F-274** | **A DOUBLE-CLICK THAT RAN HALF ITS JOB, AND A PULLER THAT SLEPT UNNOTICED.** `PUSH_TODAY.bat` in the tracker folder pushed the follow-up list and never `push_patient_join.py` — so the owner's daily double-click had never moved a Docterz visit to the VPS, and D356's consumer sat empty without anyone knowing. Separately, the medical-PC puller slept 46 minutes and no surface said so. The bat now runs both legs; the 01-Sep visits landed hands-free the next morning. Task-health shouts are carried to M6. | **A scheduled job announces its own missed heartbeat on the owner's surface; a multi-leg script reports each leg by name. "It ran" is not a status.** |
| **F-275** | **WRITTEN RECORDS OUTLIVE THE TRUTH THEY DESCRIBED.** The owner's diagnosis, stated as the marathon's mental model: feeds land late and out of order; a flag or exception written in the gap sticks after reality heals, and the surface keeps shouting a fact that is no longer true. Live-computed surfaces heal themselves; written records need an engine. `finance_heal.py` (cron `*/30 8-21`, on landing, on feed arrival, on day save, on "Recheck now") re-checks `upi_vs_statement` · `missing_day` · `MARG_DAY_NOT_FILED` · `BANKMATCH_FEED_MISSING` · `line_sum`; healed rows keep their record and stop shouting. First run healed 16; second 0. | **Never build a shouting record without its recheck. One fact shouts in one place, and any record a feed can answer must heal itself.** |

**Next free: F-276 · D361.** The S214, S215 and S216 candidate sets and F-244 remain RECORDED, NOT
MINTED — they await the owner's ruling, as before.

**END OF FAULT → ACTION REGISTER v2.48 — F-269 … F-275 are the last minted findings. The v2.45 end-marker above is retained in place as a truncation-proof. If this marker is absent, this file is truncated and must not be used as canonical.**

---
*Minted at the S219 open, 02-Sep-2026, as the S217/218 close debt. Two the assistant's own (F-269,
F-271); one the owner's (F-273); F-275 is his diagnosis written as a rule.*


---

# MINTED AT THE S219 CLOSE — F-276 … F-279

**Four findings from the Marg session. Two are the assistant's own (F-276, and F-278 is the near
miss it caught in time). F-277 is the one that matters: it is still live, and it is the first item
of S220 by the owner's instruction.** Authored from Archive §S219, never from memory.

| code | finding | the rule it leaves behind |
|---|---|---|
| **F-276** | **A SHAPE INFERRED FROM ITS OWN MAJORITY IS NOT A RULE.** The S219 returns analysis reported clinic IDs `104` and `523` as "cut or mistyped" because 68 of 70 examples had four digits. Nothing was checked against the patient master. The owner answered in one line — *"3 digit clinic id exist, check patient master"* — and Docterz has **Chetna** for ID `104`, with the books agreeing. Worse, the file that proves it (`returns_docterz_match_Aug2026.csv`) was built at S217/218 and had been sitting on the owner's own disk the whole time: the project's own prior evidence was not searched before a new claim was made. Withdrawn; the Darpan worksheet was rebuilt the same hour. The assistant's own. | **A claim about the SHAPE of data is checked against the master that defines it, never against the frequency of its own examples. And before asserting anything about a population, search this project's own prior work on it — the answer is often already on disk.** |
| **F-277** | **AN IDENTITY THAT DOES NOT AGREE WITH ITSELF IS ACCEPTED IN SILENCE — AND IS WORSE THAN NO IDENTITY.** `finance_ingest.resolve_patient()` states its own behaviour in its docstring: *"Clinic ID first, name only as a hint."* The bill's name is never compared with the master's. Measured on August: **5 of 43 returns (12%)** carry an ID belonging to someone else — `762` is Daljeet Singh while the bill is Paramjeet Kour's, `638` is Saloni Shrivastav while the bill is Samreen Rehman's, `782` is Trishna while the bill is Prem Pal Singh's, `7837` disagrees with the books, and `212` is not in the Docterz master at all. A stranger is attached **silently**, and every audit afterwards judges her returns against his purchases with full confidence. **This is strictly worse than the WALK-IN pooling of F-273**, which at least announces that it does not know. STILL LIVE. Ruled by the owner as the first build of S220 — it is a money-path change and needs his OK. | **When two identifiers arrive together, DISAGREEMENT IS A FINDING — never a tiebreak resolved in silence. A verdict may be delivered only on an identity that has agreed with itself.** |
| **F-278** | **A DISPLAY WHOSE DEFAULT BRANCH IS THE ALARM WILL ALARM ON EVERY FUTURE VALUE.** The hub's returns badge is a two-branch ladder: `ok` is green, two named verdicts are amber, **and everything else is red**. The new verdict "identity needed" — introduced precisely to STOP an accusation — would have arrived on the owner's screen in the loudest colour there is. Caught before shipping only because the screen's own code was read first (the S209 rule, applied deliberately). Fixed in the same kit. The assistant's own, caught in time. | **In any value-to-appearance map, the default branch is the one to design, not the one to leave. A new value must be a deliberate decision on the screen, never a fall-through into the loudest state.** |
| **F-279** | **A POPULATION WAS NAMED WRONG FOR FIVE SESSIONS, AND EVERY REMEDY INHERITED THE ERROR.** Documents from S213 onward called these "no-name" or "unnamed" credit notes. Measured against the source of record — Marg's own `SALE RETURN LIST`, 197 notes, 01-Apr → 02-Sep — **0 of 197 lack a name**; 127 lack an **ID**. The mis-naming shaped the remedies: worksheets asked Darpan to identify people Marg had named all along. The correct measurement also dated the break (clinic-ID capture begins Jul-2026: 0 of 43 in April, 31 of 39 in July), which is what turned a 127-row chase into a 15-row task and produced the owner's D361 cutover. | **Before designing a remedy, COUNT THE POPULATION IN THE SOURCE OF RECORD. A name for a problem is a claim about it, and a wrong name survives longer than a wrong number because nobody re-measures a word.** |

**Next free: F-280 · D362.** The S214, S215 and S216 candidate sets and F-244 remain RECORDED, NOT
MINTED — they await the owner's ruling, as before.

**END OF FAULT → ACTION REGISTER v2.49 — F-276 … F-279 are the last minted findings. The v2.48 end-marker above is retained in place as a truncation-proof. If this marker is absent, this file is truncated and must not be used as canonical.**

---
*Minted at the S219 close, 02-Sep-2026. F-276 and F-278 are the assistant's own; F-277 is still live
and opens S220; F-279 is the measurement that produced D361.*
