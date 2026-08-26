> ## WORKING PAPER — S203, not a reference
> Written to work something out on 26-Aug-2026. Its conclusions live in
> `MARG_MEDICAL_CURRENT.md`; its evidence and reasoning live in
> `MARG_MEDICAL_HISTORY.md`, both in `deploy_kits/MARG_MEDICAL/`.
> **Do not cite this as current.** Retained, not deleted (F-23).

# S203 — PENDENCY RECONCILIATION

**26-Aug-2026, Session 203. READ-ONLY.** Nothing canonical was edited, no F-number minted, no commit
made. This file is the only write.

**What this is.** `S202_PENDENCY_AUDIT.md` §6 named four gaps and left them open; `OWNER_TODO_LIVE.md`
⭐3 carries them as *"also outstanding from the S202 sweep"*. This document works each of the four to a
verdict against evidence, and recommends. **It recommends only — minting is the owner's, at a close.
Next free is F-194.**

---

## 0 · METHOD, AND WHAT IT CANNOT SEE

**Bytes read, not filenames trusted (D188).** Where a claim is about live code, I resolved the LIVE
file by its pin in `deploy_kits/KB_canon_all/live_pins_S202close.txt` (83 rows, header
`source: KB_Register_v5_54_S202.md`, `source_md5: 8fede84d7126e13fca17418e449f9d0a`,
`register_pin_verified: yes`) and then hashed the repo file that carries that md5. Every hash below
was transcribed from an `md5sum` run in this session, or from the manifest row where I say so (F-116).

**Sources swept:** the git working tree at `dr-manoj-git/drmanoj-clinic-automation` (repo bytes, all
`deploy_kits/`, `finance/`, `portal/`, `margpull/`) · `KB_History_Archive_v1_49_S202.md` (grepped, never
read whole) · `KB_Register_v5_54_S202.md` · `CANONICAL_MANIFEST.md` · `Fault_Action_Register_v2_41.md` ·
`HANDOFF_RUNBOOK` v135 and v136 · `START_HERE_SESSION_202`/`203` · and, from the Project:
`AUDIT_RUN_2026-08-24_slice1.md`, `AUDITOR_SEED_v1.md`, `S201_PARKED_BACKLOG.md`,
`S201_Medical_Pipeline_Completion_Audit.md`, `S201_Marg_Pipeline_Rebuild_Plan.md`,
`S187_Daily_Flow_v2_Design_Addendum_Returns_360.md`, `SYSTEM_DOC_COVERAGE_MAP_S147.md`.

**Hashes verified this session** (repo file → md5, my own runs):

| file | md5 | note |
|---|---|---|
| `deploy_kits/S202_B2C/finance_app.py` | `50ac4c86a3985bf82269d650d5e46f0f` | **= the live `finance_app.py` pin.** These are the bytes I read for every "is it built" question. |
| `deploy_kits/S194_TRIPLE/finance_ingest_S194.py` | `6cb83302b022ca3d46a53b32011a7ddd` | **= the live `/root/finance/finance_ingest.py` pin.** |
| `deploy_kits/S193_DISC/marg_report_S193.py` | `6411a57d4517e0a06a02e1045b354138` | **= the live `/root/finance/marg_report.py` pin** (the SERVER parser). |
| `deploy_kits/S195_MARG/marg_report.py` | `28b47d447cfd966411742055717a5c56` | the MEDICAL-PC guard's parser. |
| `finance/marg_report.py` (working tree) | `28b47d447cfd966411742055717a5c56` | stale; identical to the PC copy, **not** to the live server file. |
| `finance/finance_ingest.py` (working tree) | `2cd0f264fb1a091f3e3ec7c3f4a17438` | stale; not the live pin. |
| `finance/finance_ui/finance_entry.html` | `8ec6ad494fd6b97e5c7c70b6c42fdfc5` | **not** the live pin `92477b06…` — see AF-6. |
| `SYSTEM_DOC_COVERAGE_MAP_S147.md` | `50085e7564cb83476a6f587782143048` | matches the manifest footnote. |
| `MARG_PIPELINE_REFERENCE_v1.md` | `97b3cf73f7f83c0860bde2d911596ff7` | matches manifest row 176. |
| `MARG_PIPELINE_MAINTENANCE_FLOW_v1.md` | `c2b5251f55762490ad219b8855a18dd8` | matches manifest row 175. |
| `MARG_INGESTION_REFERENCE_v1.md` | `4d603b727a91a7c782992f092fc949e3` | matches manifest row 177. |
| `S195_Medical_Watcher_LIVE_Reference.md` | `885090ab946b61e7b5a990a14a190a15` | matches manifest row 191. |
| `S179_Finance_LIVE_State.md` | `54cb25a88adc5692360341113a87a43e` | matches manifest row 172. |
| `AUDITOR_SEED_v1.md` | `b4e349cbcf01547ff774a7c3c434bb21` | matches manifest row 192. |
| `Clinic_Source_Data_Retention_Policy_v1.md` | `90831162f985359b69725b1dc874e679` | matches manifest row 193. |
| `Fault_Action_Register_v2_41.md` | `4883e3bdf08cba92da7597448e00f2da` | matches manifest row 207. |

**What this reconciliation cannot see, stated so it is not mistaken for coverage:**

- **No live box was reached.** Nothing here confirms the VPS, the medical PC, manojz or Drive. Every
  "live" statement is *the bytes the pin list says are live*, read from the repo copy carrying that md5.
- **The repo mount is the owner's local working tree**, which `OWNER_TODO_LIVE.md` ⭐0 item 3 says may
  hold unpublished commits. It is at least as new as origin, not older — but I did not run `git status`.
- **My absence checks are filename- and token-scoped greps**, not the 26,745-file content sweep the
  Auditor ran. Where I say "found nowhere", I name exactly what I searched.
- **§S197 has no section in the Archive.** The narrative sits inside §S196 as an "S197 FOLD NOTE"
  (Archive line 6914), and the Archive's own END marker correctly omits §S197 from its enumeration —
  so this is consistent, not a stump. Noted because Thread 4 rests on Archive absence, and the reader
  should know that gap is expected.

---

## THREAD 1 · C3 – C8 FROM `S201_PARKED_BACKLOG`

`S201_PARKED_BACKLOG.md` §F asked for *"F-numbers for AF-2 and for C1–C8"*. The S201 close minted
F-179…F-183, which cover other things. C1 and C2 were fixed by `S201_HEALTH`. **The six below have no
entry in `Fault_Action_Register_v2_41.md`** — I grepped that file (`4883e3bd…`) for each; zero hits.

**Headline correction to `S202_PENDENCY_AUDIT` §6 N1: N1 lists six faults as unminted and still true.
Only four of them are still true. C5 was fixed by the same session that raised it, and C8 is not a
new fault at all — it is AF-1 under a second name.** Detail below.

### C3 — the approvals WALK-IN warning is wrong twice · **STILL TRUE** · recommend **F-number**

**Verified in the live bytes.** The live server parser is `/root/finance/marg_report.py`, pinned
`6411a57d4517e0a06a02e1045b354138`; the repo file carrying that md5 is
`deploy_kits/S193_DISC/marg_report_S193.py`. Its **line 516** still reads:

```
warnings.append("%d of %d bills carry no clinic ID and will attribute to WALK-IN"
```

**Why it is wrong twice.**
1. **It names the wrong destination.** **D348** (S201, in the Register's decisions text and in the
   manifest §S201 block) ruled that a sale bill with no clinic ID **counts in sales in full and is
   parked for the Docterz cross-match** — it is not attributed to WALK-IN, and the words *variance* and
   *low confidence* are retired. The parser was never updated. The message the owner reads on the
   approvals surface therefore states an outcome the system no longer produces.
2. **It counts from the wrong authority.** The warning is emitted inside the parser, upstream of
   `finance_ingest`, which is the component that actually decides routing and can overrule the
   parser's id count. Confirmed structurally: the string exists only in the `marg_report` family, and
   `finance_ingest.py` (live pin `6cb83302…`) carries its own `split_clinic_id` routing.

**Why it deserves a number rather than a backlog line.** D348 was applied where someone looked — the
health page and the ingestion reference — and not to the parser that prints the sentence to the owner.
That is **F-107's shape** (a ruling verified in the place it was raised, never swept for its other
instances), recurring against a *signed decision*. The one-line wording fix is trivial; the finding
worth recording is that a decision changed the system's behaviour and nothing asked what else said
the old thing.

### C4 — two parsers look for a clinic ID · **STILL TRUE** · recommend **F-number**

`split_clinic_id` is present in both live-pinned files: `deploy_kits/S194_TRIPLE/finance_ingest_S194.py`
(`6cb83302…`, the live ingest) and `deploy_kits/S193_DISC/marg_report_S193.py` (`6411a57d…`, the live
parser), as well as in the stale working-tree copies and in `S183_M2a` and `S195_MARG`.

**This is the duplicated-rule half, and it is not the same finding as B4/AF-5.** Worth separating,
because the S202 audit and the parked backlog blur them:

- **C4** = one *rule* (how a clinic ID is recognised) implemented in **two modules** on the same box.
  This is precisely the class `marg_net_sql()` was created to end at S195 (the credit-note sign counted
  twice in two of three readers). Two copies of a rule drift by editing, not by deployment.
- **B4 / AF-5** = one *file* at **two versions on two machines** (`6411a57d…` server vs `28b47d44…`
  medical PC). That drifts by deployment.

Both are live. **F-183** already sits OPEN-by-choice over the clinic-ID matching tiers and single-digit
IDs; C4 is the structural cause underneath it and belongs beside it in the register, so the eventual
kit fixes the class rather than one tier.

### C5 — the medical guard cannot run at all · **NO LONGER TRUE AS WRITTEN** · recommend **nothing for C5; one new candidate in its place**

**This is the correction.** C5 was written mid-S201 and overtaken by that same session's work. The
Archive records the fix explicitly (`KB_History_Archive_v1_49_S202.md`, §S201 "**THE `.xlsx` TIME BOMB,
REMOVED RATHER THAN MANAGED**", around line 7107):

> *"Rather than install and then maintain `openpyxl` on a machine nobody logs into, the dependency was
> **deleted**: `xlsx_stdlib.py` (`bbe11a8953f66c27126c48e773cfbe35`) reads `.xlsx` with `zipfile` +
> `ElementTree` and nothing else, validated cell-for-cell against `openpyxl` on the real exports.
> `marg_router.open_sheet()` routes to it; **the medical kit carries it**."*

*(That md5 is transcribed from the Archive, not re-hashed by me — see the new candidate below for why
I could not re-hash it.)*

**So C5 should be marked SUPERSEDED in `S201_PARKED_BACKLOG`, not minted.** Minting it would put a
fixed fault in the register — the mirror image of F-108, and worse, because it would read as open.

**But two things in C5's neighbourhood are true, and neither is C5:**

**(a) NEW CANDIDATE — five live PC-side files exist nowhere in the repo.** I searched the whole mounted
tree by filename for each. Results:

| file | in repo? |
|---|---|
| `marg_gate.py` | yes — `deploy_kits/S202_PICTURE/marg_gate.py` |
| `pipeline_status.py` | yes — `deploy_kits/S202_B2B/pipeline_status.py` |
| `xlsx_stdlib.py` | **no match anywhere** |
| `medical_agent.py` | **no match anywhere** |
| `marg_rescan.py` | **no match anywhere** |
| `medical_inventory.py` | **no match anywhere** |
| `medical_census.py` | **no match anywhere** |

All seven are named together as live tooling in Archive §S201 (line 7255: *"Manojz tooling (not VPS,
not manifest rows): `marg_gate.py` · `marg_rescan.py` · `xlsx_stdlib.py` · `medical_inventory.py` ·
`medical_census.py` …"*), and `medical_agent.py` is pinned in the same passage at **S201.11
`69e60d778ab61a8d50c79394e2951309`** (Archive value, not re-hashed by me). Two of the seven are
published; five are not. There is **no S201 medical/manojz kit in `deploy_kits/`** at all — only
`S201_A1FIX`, `S201_HEALTH`, `S201_UI`, all VPS.

This is **AF-6's class at five-file scale**: bytes that exist only on a machine, with no off-box copy,
for code that supervises the pharmacy capture chain. AF-6 at least had a proven two-step recovery
recipe; these have none recorded. Note this is not a PHI exclusion — `margpull/` and both S202 PC kits
*are* published, so the rule is being applied inconsistently rather than deliberately.
**Recommend: one F-number.** Caveat: my check is filename-scoped in the working tree; a content sweep
inside kit tarballs (as the Auditor ran for AF-6) would make the absence airtight.

**(b) Two canonical documents place `xlsx_stdlib.py` on different machines.**
`HANDOFF_RUNBOOK_2026-08-25_Session201close_v135.md` line 55 says it *"replaced `openpyxl` **on the
medical PC**"*; Archive line 7255 files it under *"**Manojz** tooling"*. Both are canonical and current
for their tier. Small, but it is the D188 family and it matters if someone ever has to rebuild either
machine. **Recommend: a documentation correction owed at a close, not a number.**

### C6 — a re-apply wipes that day's review queue · **STILL TRUE** · recommend **F-number, the highest-priority of the six**

**Verified in the live bytes.** `deploy_kits/S194_TRIPLE/finance_ingest_S194.py` = `6cb83302…` = the
live `/root/finance/finance_ingest.py` pin. **Line 416**:

```
con.execute("DELETE FROM sale_item_review WHERE ingest_batch_id=?", (old[0],))
```

Present unchanged in the stale working-tree copy too (`finance/finance_ingest.py:358`).

**Why this one first.** It is the only member of C3–C8 that **destroys work a human did**. Every other
item is a wrong message, a duplicated rule, a missing check, or an accepted risk. And it sits directly
across the path of the flagship blocked item: `OWNER_TODO_LIVE.md` ⭐3 and `S202_PENDENCY_AUDIT` X1
both plan the **Docterz EMR cross-match** over the 49 parked bills (₹51,868) using
`bill_date + patient_name + phone_last4`. The entire value of that work is resolutions attached to
parked rows — and a re-apply of that day deletes them, silently, with no surviving record. Both
documents already know this (X1 says *"a re-apply wipes that day's parked list, so resolutions need
somewhere that survives a re-import"*) — **it is a stated design constraint on a flagship build that
has no register entry.** That is the gap worth numbering.

### C7 — no PC-side live pins · **STILL TRUE IN SUBSTANCE, PARTIALLY MITIGATED** · recommend **F-number, on precedent**

`live_pins_S202close.txt` now carries **20 BLIND rows**, five of which are manojz files added at S202:
`marg_gate.py` (`af2c3ca507136f3f82ec7cf64e8aae34`), `pipeline_status.py`
(`51cf10c9f2543fcd48a61ee7f8faf51a`), `PULL_FROM_MEDICAL.bat` (`3c5389d54241f234e94dc62b82d046e1`),
`signatures.json` (`3e9cbba02ffb4e0f131738eee7a465f7`), `_coverage_from.txt`
(`0652d17074be03e3c575f423a9c82e12`). *(Transcribed from the pin list; not re-hashed against either PC,
which I cannot reach.)*

**But BLIND is not verification.** The file's own header defines it:

> `# BLIND  = listed every run as NOT verified; never counted as a pass`

And I read all 20 BLIND rows: **not one names a medical-PC file.** No `medical_agent.py`, no medical
`marg_watch.py`, no `GUARD_AND_SEND.bat`, no `SEND_TO_CLINIC.bat`, no medical `marg_report.py`. (The
one PC-side row, `docterz_report.py`, is the owner's tracker PC.) **The machine where C4/AF-5's
two-build drift actually lives has no pin of any kind, blind or otherwise.**

**Why a number rather than a backlog line.** The instinct is "this is a missing capability, not a
fault — `verify_live_pins.py` never claimed to reach the PCs." But that is exactly the argument the
project has twice rejected: **F-99** (an alarm anchored on `MIN(business_date)` cannot see a unit that
never filed a first day) and **F-107** (Phase 0 is blind to a document that was never listed) are both
"the checker's scope was never asked about." The precedent is settled, and C7 is the same shape one
estate wider. It is also, on the S201 record's own words, *"how C4's two-build drift went unnoticed"* —
so it is the enabling condition for two of the others and should be numbered beside them.

### C8 — AF-1 still armed on the medical sender · **STILL TRUE, DELIBERATELY** · recommend **no separate number — resolve it through the AF↔F bridge (Thread 2)**

**C8 is AF-1.** Not "the same shape as" — the same finding, re-described. Compare
`S201_PARKED_BACKLOG` C8 with `AUDIT_RUN_2026-08-24_slice1.md` §AF-1: same file
(`SEND_TO_CLINIC.bat`), same mechanism (curl does not overwrite `last_response.txt` on failure →
false ACCEPTED → md5 appended to `sent_hashes.txt` → permanent local refusal to resend).

It is **already recorded in five canonical or current places**, and as an accepted risk, not an
oversight:

- `MARG_PIPELINE_REFERENCE_v1.md` line 99 (Tier 1, `97b3cf73…`)
- Archive §S201 line 7277, **inside D347's own decision text**: *"The manual sender on the medical PC
  stays as the fallback and is never removed (AF-1 remains armed on it — deliberately, and recorded)."*
- `CANONICAL_MANIFEST.md` §S201 block (same clause)
- `HANDOFF_RUNBOOK` v135 line 124 and v136 line 108 (⭐3 blocked)
- `OWNER_TODO_LIVE.md` ⭐3
- and `S201_Medical_Pipeline_Completion_Audit.md` §8, "what is still true and unfixed"

Minting a *C8* number would put a second identifier on a finding that already has one (AF-1) and is
covered by a signed decision (D347). **The right resolution is the bridge**: give AF-1 an F-number as
part of Thread 2's reconciliation, mark it OPEN-BY-CHOICE with D347 as the authority, and strike C8
from the parked backlog as a duplicate.

### Thread 1 recommendation, in one table

| ref | still true? | recommend | why |
|---|---|---|---|
| **C6** | **yes** (live bytes, line 416) | **F-number — first** | the only one that destroys human work; a stated blocker on the Docterz flagship with no register entry |
| **C3** | **yes** (live bytes, line 516) | **F-number** | contradicts signed D348 in the owner's own approval surface; F-107's shape against a decision |
| **C4** | **yes** (both live pins) | **F-number** | duplicated rule — the exact class `marg_net_sql` exists to end; sits under F-183 |
| **C7** | **yes** (0 medical-PC pins; 5 manojz rows, all BLIND) | **F-number** | precedent F-99 / F-107; the enabling condition for C4 and AF-5 |
| **C5** | **no — fixed at S201** | **nothing; mark SUPERSEDED** | the fix shipped in the session that raised it (Archive §S201) |
| **C8** | **yes, deliberately** | **nothing separate — fold via AF-1** | it *is* AF-1; already carried in five places under D347 |
| *(new)* | five live PC-side files absent from the repo | **F-number** | AF-6's class at five-file scale, on the pharmacy capture chain |

**Count: four of C3–C8 deserve F-numbers, plus one new candidate that came out of checking C5.**

---

## THREAD 2 · THE AF-# SERIES AND ITS MISSING BRIDGE

### The complete AF list, and where each actually lives

**The series is AF-1 … AF-6, and it is complete as of today.** Provenance: one audit run exists,
`AUDIT_RUN_2026-08-24_slice1.md` (run 1, slice 1, 24-Aug-2026), which states *"slice 1 produced 2 high,
2 medium, 2 low candidates"* — six — and closes *"Next run: slice 2 — the UPI/bank witness chain (and
re-execution of AF-1…AF-6 evidence first)."* The Auditor is scheduled weekly, Mondays ~07:05 IST
(trigger `trig_01XBRt7dcsXcjtmgdmemnR3x`, Archive line 6904); 24-Aug was the first Monday and the next
is 31-Aug, still in the future. I searched the Project and the repo for any second run file
(`AUDIT_RUN*`): **none exists.**

| ref | sev | what it is | recorded where | status today | folded into an F-number? |
|---|---|---|---|---|---|
| **AF-1** | HIGH | `SEND_TO_CLINIC.bat` can report ACCEPTED for a report that never left (curl leaves `last_response.txt` untouched on failure), then appends the md5 to `sent_hashes.txt` and refuses to ever resend it | audit run · `MARG_PIPELINE_REFERENCE_v1` L99 · Archive L7277 (inside D347) · manifest §S201 · Runbook v135 L124 / v136 L108 · `OWNER_TODO_LIVE` ⭐3 · `S201_PARKED_BACKLOG` C8 · `S201_Medical_Pipeline_Completion_Audit` §8 | **OPEN BY CHOICE** — kept as the only medical-side fallback; `marg_gate.py` is the safe path | **NO.** Zero rows in `Fault_Action_Register_v2_41`. Cited twice as a *class* ("AF-1's exact shape", of our own installer v2 at S201) — a comparison, never a fold |
| **AF-2** | HIGH | `TOTAL_VS_MARG` born dead at S195 — reader wants `business_date`/`net_p`, writer stores `date`/`expect`; never fired once | audit run · Register v5.46 + live-file table L155 · Archive L7252 · manifest §S201 + L1161 · Register v5.51/v5.52 (as precedent) · **Fault Register v2.41, inside F-191's text** | **CLOSED at S201** by kit `S201_A1FIX` (`2c99b2c6…`→`d930b6b5…`, smoke 680→683) | **NO.** `S201_PARKED_BACKLOG` §F asked for it explicitly; the close minted F-179…F-183, none of which is AF-2. F-191 (S202) says *"AF-2 was the same shape"* — precedent, not identity |
| **AF-3** | MED | a failed approval can leave a posted staff-ledger advance behind; the retry posts it again (`append_ledger` writes durably before the finance commit; rollback drops the stamp, not the JSONL row) | audit run · `S201_PARKED_BACKLOG` §E · `S202_PENDENCY_AUDIT` O9 · `OWNER_TODO_LIVE` ⭐0 #7 + ⭐2 · Runbook v135 L87/L118, v136 L88 · `START_HERE_SESSION_202`/`203` L127 | **UNTRIAGED; owner scan owed before the August close** (command in the audit run §Commands 2) | **NO.** Zero rows |
| **AF-4** | MED | five checker-grade routes unscoped — any medical-unit login can pull month totals, day-wise closings, the owner's drawings and patient names by URL | **audit run · `S201_PARKED_BACKLOG` §E — and nowhere else** | **UNTRIAGED** | **NO.** Zero rows |
| **AF-5** | LOW | the medical-PC guard runs a different parser than the server while claiming identical judgment (PC `28b47d44…` S180 vs server `6411a57d…` S193) | **audit run · `S201_Marg_Pipeline_Rebuild_Plan.md` row K — and nowhere else.** *Absent from `S201_PARKED_BACKLOG` §E* | **STILL TRUE — I re-verified it by md5 this session** (see below) | **NO.** Zero rows |
| **AF-6** | LOW | one live pin's bytes exist nowhere off the box as a file: `finance_entry.html` `92477b06…` | **audit run · `S201_PARKED_BACKLOG` §E — and nowhere else** | **STILL TRUE** — I hashed the only `finance_entry.html` in the repo: `8ec6ad494fd6b97e5c7c70b6c42fdfc5`, not the pin. `deploy_kits/S193_UX/patch_pages.py` is present, so the two-step recovery still works | **NO.** Zero rows |

**AF findings that exist ONLY in an audit run file and nowhere in the canon: AF-4, AF-5 and AF-6.**
I grepped the entire repo for `AF-[4-9]` across `*.md`, `*.txt`, `*.py`, `*.html`, `*.js`, `*.gs`:
**zero matches.** AF-4 and AF-6 at least reached `S201_PARKED_BACKLOG` §E, which is a Project doc, not
canon. AF-5 did not even reach that.

### AF-5 is not unaccounted for — it was dropped in transcription

`S202_PENDENCY_AUDIT` §6 N2 says *"AF-5 is unaccounted for in any document I can reach."* **That is
resolved.** AF-5 is written out in full in `AUDIT_RUN_2026-08-24_slice1.md`, between AF-4 and AF-6, with
its own heading, class, evidence and severity. What happened is narrower and more instructive:
`S201_PARKED_BACKLOG` §E — the doc that transcribed the Auditor's findings for triage — lists **AF-3,
AF-4 and AF-6 and silently skips AF-5.** Everything downstream read §E, not the run, so the label
vanished from the project's working memory while the run file sat unchanged.

**The fault itself was never lost, only its name.** AF-5's substance survives under two other
identifiers raised independently the same session: `S201_PARKED_BACKLOG` **B4** ("One parser, not
three", which quotes both md5s) and **C4**. And I re-verified the underlying condition today:

- live server parser: `/root/finance/marg_report.py` pinned `6411a57d4517e0a06a02e1045b354138`
  = `deploy_kits/S193_DISC/marg_report_S193.py`
- medical-PC guard parser: `deploy_kits/S195_MARG/marg_report.py` = `28b47d447cfd966411742055717a5c56`

Two builds apart, exactly as AF-5 stated, eight sessions later. **AF-5 should be recorded as STILL
TRUE and re-verified, not as missing.**

### The bridge: why it does not exist, and what it should be

This is the root cause, and it is documentary rather than accidental.

**`AUDITOR_SEED_v1.md` (`b4e349cb…`, Tier 1, manifest row 192) says, under Rules of evidence:**

> *"Register format: continue the existing **F-##** series (Fault_Action_Register)."*

**The scheduling override at S196 changed that.** Archive line 6904:

> *"Weekly unattended cloud run … seeded from `AUDITOR_SEED_v1.md` + unattended adjustments (slice
> rotation from `AUDIT_RUN` docs; **AF-# numbering, so the Auditor never mints bare F-numbers**; an
> owner-commands section instead of pause-for-paste …)"*

The reason is sound: an unattended weekly agent must not consume numbers from a series a human close
also mints from — that is the F-155/F-160 fork the S197 fold had just spent a session reconciling. **But
the override replaced a rule that ended in the register with a rule that ends nowhere.** The seed's
sentence was overridden; no sentence replaced it. There is no step in `END_OF_SESSION_PROMPT_v7`, and
no line in the seed, that says *at a close, triage the open AF findings and mint or dismiss each one*.
The Auditor's own instruction — *"Findings go to the owner for triage, never straight to the backlog"* —
names a destination that has no arrival procedure.

The result is measurable: **six findings, one of them HIGH and closed by a shipped kit, one of them
HIGH and still armed in production, and the F-register — the project's answer to "what is wrong with
this system" — contains none of them.** `Fault_Action_Register_v2_41` runs F-0…F-193 and mentions an
AF token exactly once, in passing, inside F-191's prose.

**Recommended shape (for the owner's decision, not applied here):**

1. **Mint the backlog at one close.** Six numbers from F-194, one per AF finding, each carrying its
   status as already established: AF-2 **CLOSED** (kit `S201_A1FIX`, with the pin chain); AF-1 **OPEN BY
   CHOICE** with **D347** cited as the authority (and `S201_PARKED_BACKLOG` C8 struck as its duplicate);
   AF-5 **OPEN, re-verified S203, by md5**; AF-3, AF-4, AF-6 **OPEN, untriaged**. Minting a closed
   finding is correct here — the register's job is the history of what was wrong, and AF-2 was wrong
   for five sessions.
2. **Add the missing step to `END_OF_SESSION_PROMPT`.** A numbered step in the same family as A8b: *every
   open AF finding is either minted with an F-number or explicitly dismissed with a reason, at the
   close.* Without a numbered step this recurs — which is the whole content of **F-108**, and F-108 has
   now recurred twice on this exact seam (N1 and N2 of the S202 sweep are both instances).
3. **Correct the seed.** `AUDITOR_SEED_v1` still tells the Auditor to continue the F-series. It is Tier 1
   and manifest-pinned (`b4e349cb…`), so a correction is a versioned change with a new hash — but leaving
   it is a canonical document instructing a live weekly agent to do the thing the project decided it
   must not do. **This is the F-23 situation and should be flagged for the owner's ruling, not
   silently edited.**
4. **One line in the register's own header** naming AF-# as a feeder series and pointing at the run
   files, so a future reader finds the second series instead of discovering it as a gap.

---

## THREAD 3 · FIVE MISSING COVERAGE-MAP ROWS — DRAFT ONLY

`SYSTEM_DOC_COVERAGE_MAP_S147.md` (`50085e7564cb83476a6f587782143048`, hashed this session; matches the
manifest footnote) carries 23 rows across four sections and **has no row for clinic-finance, Marg
capture, the medical PC, manojz or the Lab PC.** It is dated S147; the entire clinic-finance estate was
built from S179 onward. The manifest already admits one of the five in its own footnote (line 298):

> *"(The clinic-finance subsystem's authoritative doc is `S179_Finance_LIVE_State`; add its row when the
> coverage map is next rebuilt.)"*

`MARG_PIPELINE_REFERENCE_v1` states the consequence bluntly in its own opening: *"The coverage map
predates this entire estate. A new engineer following the old pointers landed on a stale or missing
document at three turns out of four."*

**Below are the five rows I would add.** Every md5 was hashed by me this session and matched its
manifest row. **Draft only — the map is not edited by this session.**

### Row 1 — clinic-finance

| System | Repo | Authoritative doc | Status |
|---|---|---|---|
| **Clinic-finance (Sanjeevni + clinic daily money: entry · approvals · day page · health · month close)** | `finance/` *(working tree S180/S182-stale — the LIVE bytes are recovered by md5 from `deploy_kits/`, per the live pin list)* | `S179_Finance_LIVE_State` (`54cb25a8…`) for the subsystem architecture and D313 invariants · **`KB_Register` (current) live-file table + `live_pins_S202close.txt` for what is live NOW** · `MARG_INGESTION_REFERENCE_v1` (`4d603b72…`) for the ingestion path | ⚠ **scattered — consolidation candidate.** The manifest names `S179_Finance_LIVE_State` as the authoritative doc, but it is S179-era: it cannot answer what is live today, because ~23 sessions of pins have moved since. The living answer is the Register's live-file table, which is not a *subsystem reference*. **This is the project's largest daily-use system and it has no wholesome single reference.** |

*Honest note the row must carry: naming `S179_Finance_LIVE_State` alone would send a reader to a
document that is authoritative on design and out of date on state. The row must name both, and say
which answers which question.*

### Row 2 — Marg capture & transport

| System | Repo | Authoritative doc | Status |
|---|---|---|---|
| **Marg pharmacy feed — capture → route → archive → send (medical PC → manojz → VPS)** | `margpull/`, `deploy_kits/S195_MARG`, `deploy_kits/S202_PICTURE`, `deploy_kits/S202_B2B` | **`MARG_PIPELINE_REFERENCE_v1` (`97b3cf73…`) — how it works** · **`MARG_PIPELINE_MAINTENANCE_FLOW_v1` (`c2b5251f…`) — the operational half: 60-second check, faults by symptom** | ✅ wholesome pair (S201, corrected S202). **Supersedes `S195_Medical_Watcher_LIVE_Reference` (`885090ab…`), whose manifest row still reads "SOLE reference for the Marg capture pipeline" — that label must be struck when this row is added** *(= `S202_PENDENCY_AUDIT` N3, unresolved)* |

### Row 3 — the medical PC

| System | Repo | Authoritative doc | Status |
|---|---|---|---|
| **The medical PC (Marg host: `medical_agent.py` supervisor · `marg_watch.py` · the guard/sender chain · two Marg output trees, `D:` and `C:\Users\Public\MARG\`)** | `deploy_kits/S195_MARG` *(guard + parser only)* — **`medical_agent.py`, `xlsx_stdlib.py` and the S201 medical tooling are in NO repo path** | `MARG_PIPELINE_REFERENCE_v1` (`97b3cf73…`) §capture · **D347** (Archive §S201, the pipeline architecture: Drive-for-Desktop bidirectional, Tailscale read-only and not load-bearing, the agent supervises but never self-updates) · `MARG_PIPELINE_MAINTENANCE_FLOW_v1` (`c2b5251f…`) for symptoms | 🟡 **operational-only, with a recovery gap.** No pin of any kind covers this machine (Thread 1, C7) and five of its live files have no off-box copy (Thread 1, C5(a)). **AF-1 remains armed here by choice, under D347.** |

### Row 4 — manojz

| System | Repo | Authoritative doc | Status |
|---|---|---|---|
| **manojz (the owner's PC: publisher + 10-minute puller + mirror + offsite, all in one box)** | `margpull/` · `deploy_kits/S202_PICTURE` (`marg_gate.py`) · `deploy_kits/S202_B2B` (`pipeline_status.py`) · `PUBLISH_ALL.bat` (D328) | **`MARG_PIPELINE_MAINTENANCE_FLOW_v1` (`c2b5251f…`) — the 60-second check's three files all live here and none needs a login** · `MARG_PIPELINE_REFERENCE_v1` (`97b3cf73…`) §transport · **D328** for publishing | 🟡 operational. **Named single-point-of-failure**: the Auditor's Surface B records manojz as *"publisher + puller + mirror + offsite in one box"*, which is audit **slice 4**'s subject and has not been run. |

### Row 5 — the Lab PC / Labmate

| System | Repo | Authoritative doc | Status |
|---|---|---|---|
| **Lab PC / Labmate (pathology)** | — none | **NONE.** The only canonical document that names Labmate at all is `Clinic_Source_Data_Retention_Policy_v1` (`90831162…`), and only for source-export retention — it says nothing about the machine, the export, or the ingest path | ⚠ **NOT A SYSTEM YET — survey owed before any build.** Carries a standing warning: **S181 records that the revenue arithmetic is INVERTED between medical and clinic/lab** — *"the single most dangerous copy-paste in the build"*. Attach a source as a *profile + signatures*, never a copied script; and **ask where Labmate writes** — Marg turned out to have two output trees on two drives. Blocked item in `OWNER_TODO_LIVE` ⭐3. |

*I searched the manifest for `Labmate`, `lab pc`, `pathology` and for any `S181_*` lab document row.
The single hit is the retention-policy row above. The Lab PC row is therefore honestly a row that says
"there is no reference" — which is more useful than its current absence, because absence reads as
"not a system", and it is a planned one.*

---

## THREAD 4 · THE LATER DAILY FLOW V2 STAGES

### What the contract actually lists

From the Register's decisions index, **D326**: *"Stages: D1 Day Page + approvals (shipped) · D2 the
maker mirror · D3 the Ledger bridge (gated) · D4 home/procedure medicine (B4) · D5 feeds/nudges/
month-pack."* Plus **D327** (the `counter` role) which *"builds with stage D-R (returns at reception)
at S188"*, **D-R** itself (specified in `S187_Daily_Flow_v2_Design_Addendum_Returns_360.md` §1), the
**360 wiring** (§3), the **orthotics purchase side** (§4 + §8 Q2), and **D6** (§9, contextual per-user
instructions).

The S187 close set the order explicitly (Archive line 6184): *"S188 opens on the signed Daily Flow v2
contract: **D-R returns → D2 mirror → 360 wiring → orthotics (asset-app purchase feed) → D5 feeds → D6**,
plus the gated §4a Staff Ledger check, the `counter` role build, and the Tailscale+RustDesk rollout."*

S188 built D2 — and **took the second item on that list, not the first.** D-R was skipped at the very
first session that ran on the signed order, and nothing recorded the skip.

### Where I looked

1. **The Archive** (`KB_History_Archive_v1_49_S202.md`), for `D-R`, `360 wiring`, `orthotic`,
   `stage D5`, `stage D6`, `counter role`, `refill-skip`. Every hit is at or before **line 6190**
   (§S188's header). Scanning everything after line 6300 — i.e. §S188-POST, §S188-FINAL, §S189, §S190,
   §S191, §S192, §S193, §S194, §S195, §S196 + the S197 fold note, §S198, §S199, §S200, §S201, §S202 —
   returns **zero matches for any of those tokens.**
2. **`KB_Register_v5_54_S202.md`**, for `D326`/`D327`: the newest hit is the S189 row confirming the
   D326(c) ₹70,000 gate verification. No stage after D2 appears in any version block v5.30 → v5.54.
3. **The live code**, `deploy_kits/S202_B2C/finance_app.py` = `50ac4c86a3985bf82269d650d5e46f0f`
   = the live `finance_app.py` pin.

### The verdicts

| stage | verdict | evidence |
|---|---|---|
| **D-R — returns booked at reception** | **NOT BUILT** | Live bytes: no `/finance/returns` route, no reception returns surface, no eligibility-legend logic, no return-slip print. **The `finance_returns` module in the live app is a different thing** — it is the S180-era ingestion of Marg credit notes from the export (`finance_returns.load_lines`, called from the ingest/apply paths). D-R is the *reception-side* flow that would give a CN something to reconcile against. Its whole point — two independent records by construction — does not exist. Archive: no mention after S187. |
| **D327 — the `counter` role** | **NOT BUILT** | Live bytes, decisive: `FINANCE_ROLES = ("maker", "checker", "viewer")` (line 308). No `counter`. The only `counter` tokens in the file are the custody **party** name (`PARTIES = ("counter", "drawer", "dr_bhawna", "dr_manoj", "bank")`, line 2313) — an unrelated use of the word. **D327 is a minted, indexed decision that was never executed**, and its build was tied to D-R, which was skipped. |
| **360 wiring** (Sanjeevni strip in the Console, refill-skipper list) | **NOT BUILT** | Live bytes: no `refill`, no 360 route. The only `360` in `portal/portal.py` is an unrelated tile string ("Track360 — 2 vehicles"). Archive: no mention after S187. The Call Console spec v2.4 §4.4 placeholder this was to close is presumably still a placeholder — *I did not open the Console spec to confirm that, so treat the placeholder's current state as unverified.* |
| **Orthotics — purchase side** | **NOT BUILT** (the sales side **IS** built) | The distinction matters and no document draws it. `/finance/api/orthotics` exists in the live bytes (line 4537), and its own docstring says *"S187_H1a; **stage D4 pulled forward at the owner's direction**"* — it is the **sales-velocity** view: owner-editable keyword vocabulary as a setting, 90-day per-item rollup, qty deliberately not summed. **The purchase side — the addendum §8 Q2 ruling that orthotics stock = scanned purchase quantities − Marg-line sales, fed by the asset app's Scan Purchase pipeline — has no code and no mention after S187.** So the reorder signal, which needs both sides, cannot exist. |
| **D5 — feeds / nudges / month-pack** | **NO EVIDENCE either way — and the one part I can trace was overtaken** | No `stage D5` mention after S187. But D5's named content was the **Yes Bank statement auto-feed** (D326(d): statements arrive in the owner's personal Gmail; the feed lands at D5 *"by forward-rule into clinic Gmail or a scoped personal-account script"*). **S195 built "the bank-statement chain end-to-end"** (Archive §S195 header) and the Yes Bank upload + reconcile path is live. So D5's bank leg appears to have been **satisfied by other work under a different name** — but *no document says so*, and the **nudges** and **month-pack** legs I found no trace of at all. I am not calling this SUPERSEDED, because the supersession is my inference from two headers, not a record. **Verdict: NO EVIDENCE; the bank leg is probably absorbed into S195, unconfirmed.** |
| **D6 — contextual per-user instructions** | **NOT BUILT** | Recorded once, at its birth: Register v5.21 (S187) — *"the owner's contextual per-user instructions idea recorded as stage D6 in the design addendum"* — and addendum §9, which is explicit that it is *"NOT scheduled; revisit at the S188 contract."* No mention anywhere after S187. It was never scheduled, so this is the mildest of the six: a parked idea, correctly parked, that simply has no status line. |

### What this thread is really about

**Four minted-or-signed items — D-R, D327, the 360 wiring, and the orthotics purchase side — are
neither built nor cancelled, and no document has said anything about them for fourteen sessions.**
D327 is the sharpest case: it sits in the Register's **decisions index** as a minted decision, which
is the project's strongest form of record, and it has never been executed. There is no mechanism that
would ever notice this — the decisions index records that a decision was *made*, not whether it was
*done*, and the backlog documents were rebuilt from session to session by carrying forward what the
previous session was working on. Everything the S187 close listed as "S188 opens on…" fell out of the
carry-forward the moment S188 built its second item and closed.

That is **F-107's family again, aimed at decisions rather than documents**: nothing asks whether a
signed stage list was ever completed. If the owner wants one durable fix out of this whole
reconciliation, a **status column on the decisions index** — built / not built / superseded, with the
session — would have surfaced all four of these years before anyone went looking.

**Recommendation: not F-numbers.** These are unbuilt scope, not faults. They belong in
`OWNER_TODO_LIVE` ⭐1 or in a revived Daily Flow v2 line with an explicit owner ruling on each:
**build, or cancel on the record.** The one thing that should not happen again is a fifteenth session
of silence, because silence here is indistinguishable from a decision.

---

## SUMMARY OF RECOMMENDATIONS

**None of this is applied. Next free F-number is F-194; minting is done at a close.**

| # | recommendation | kind |
|---|---|---|
| 1 | Mint **C6** (re-apply wipes the review queue) — first; it blocks the Docterz flagship | F-number |
| 2 | Mint **C3** (WALK-IN warning contradicts D348) | F-number |
| 3 | Mint **C4** (clinic-ID rule duplicated across two live modules) | F-number |
| 4 | Mint **C7** (no medical-PC pins at all; manojz rows are BLIND, which is not verification) | F-number |
| 5 | Mint the **five unpublished PC-side files** (`xlsx_stdlib.py`, `medical_agent.py`, `marg_rescan.py`, `medical_inventory.py`, `medical_census.py`) | F-number |
| 6 | Mark **C5 SUPERSEDED** in `S201_PARKED_BACKLOG` — fixed by the session that raised it | doc correction |
| 7 | Strike **C8** as a duplicate of **AF-1**; resolve via the bridge | doc correction |
| 8 | **Mint AF-1…AF-6** with their established statuses (AF-2 CLOSED; AF-1 OPEN-BY-CHOICE under D347; AF-5 OPEN, re-verified S203) | F-numbers ×6 |
| 9 | Add a numbered **AF-triage step** to `END_OF_SESSION_PROMPT` — mint or dismiss every open AF at each close | routine change |
| 10 | **Flag `AUDITOR_SEED_v1` for the owner's ruling** — it still instructs the live weekly Auditor to continue the F-series, which S196 overrode (F-23 situation: flag, do not silently edit) | owner ruling |
| 11 | Add the **five coverage-map rows** drafted in Thread 3, and strike the *"SOLE reference"* label on `S195_Medical_Watcher_LIVE_Reference` when Row 2 lands (= N3) | doc rebuild |
| 12 | Correct the `xlsx_stdlib.py` machine contradiction between Runbook v135 L55 and Archive L7255 | doc correction |
| 13 | Get an **owner ruling — build or cancel on the record** — on D-R, D327, the 360 wiring and the orthotics purchase side | backlog / ruling |
| 14 | Consider a **built/not-built status column on the decisions index** — the only proposed change here that would have caught Thread 4 unaided | structural |

---
*S203 pendency reconciliation · read-only · every live claim resolved to a pin and hashed this session ·
absences stated with what was searched · four of C3–C8 recommended for numbers, C5 corrected as fixed,
C8 corrected as a duplicate.*
