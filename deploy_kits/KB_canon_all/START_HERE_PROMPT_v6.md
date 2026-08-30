# START-HERE PROMPT — v6 — paste to begin a new session

> **v6 change (S207): the fourth store is named here, with its REAL path.** The canonical set lives
> in this Project's knowledge; code lives in **GitHub**; and everything canon deliberately excludes
> lives in **`D:\Downloads\ClaudeCowork\`** on manojz — reachable in Cowork whenever the
> **Downloads** folder is connected, which is how this project is normally worked.
>
> **The S206 close wrote that path as `D:\ClaudeCowork\` in three places** — this prompt's
> predecessor, `COWORK_FOLDER_INDEX.md`, and step A12 of the close-out routine. It is wrong in all
> three. A session that trusted it recorded A12 as un-runnable while the folder sat, connected, one
> level down. **A path in a document is not provenance either (D188's shape, one store over).**

---

Hi Claude. Continuing my clinic-automation project (**Session __ — use the next number**).
I'm Dr. Manoj Agarwal, orthopaedic surgeon, Advanced Orthopaedic Surgery Centre, Bareilly.
Solo practice, older Hindi-first semi-urban patients.

**Working protocol (follow strictly):**
- Plain language, no assumed coding knowledge.
- ONE step at a time — wait for my explicit confirmation before the next.
- Full-file replacements only, never diffs I have to hand-edit.
- ALL-CAPS from me = urgent.
- Mask all patient numbers (last-4 only) and all secrets/tokens — never print them.
- **F-185, as the owner settled it on 28-Aug-2026: NO PATIENT NUMBER in the repository,
  enforced from that date forward.** History is left as it is — the canon has carried 9 numbers
  across 30 documents since July, and *a rule the codebase has always violated is a rule people
  learn to ignore.*
  **Enforced as "no number at all"**, because nothing in the text says whose a number is, and a
  missed supplier number costs a line while a missed patient number cannot be taken back.
  Numbers live in `D:\Downloads\margsync\_config\`. The gate runs on the **staged** files only —
  which is what makes the date line structural rather than a setting — and
  `NO_PHONE_NUMBERS.py --fix` masks a number in prose (`93xxxxxx80`) when that is the right answer
  instead of moving the file.
- Nothing already live is rebuilt without my explicit OK. Manual workflow always stays as fallback.
- Build/test offline → py_compile (I use `python`, not `python3`) → then I install.
- For VPS python, always use `/root/wa/venv/bin/python3` (system python3 lacks gspread).

**Ending a session:** say **"EOS"** (full close-out, code changed) or **"EOS-light"**
(fold-in/documentation session, no code touched). The routine is canonical in project knowledge as
**`END_OF_SESSION_PROMPT_v10.md`**.

---

## Phase 0 — do this FIRST, every session. Verification before work.

1. **CHECK THE FOLDERS AND THE DISK — AND PROMPT ME. Do this before anything else, every time.**

   Report exactly what is connected and what is missing, then ask for what is missing rather than
   working around it:

   | needed | what breaks without it |
   |---|---|
   | **`D:\Downloads`** | no Marg archive, no `_config` store, **no ClaudeCowork** — the KB extension |
   | **`D:\dr-manoj-git`** | no repository, no kits, no publish |
   | **`F:\ClinicBackup`** (the 1 TB SSD) | the close cannot mirror or take a cold kit |

   **The SSD is usually NOT connected** — it is a disk I plug in. Say so plainly and ask, rather
   than reporting a step as un-runnable. *Half the stores being present is how two copies of one
   document get made.*

   ⚠ **`F:\ClinicBackup` does not mount in the device shell.** It is reachable only by
   `device_list_dir` / `device_stage_files` / `device_commit_files`, so anything going onto it is
   written as a **single archive**, never synced file-by-file.
2. Open **`CANONICAL_MANIFEST.md`** (Tier 0 · the linchpin). It lists every canonical doc, its tier
   and its md5.
3. **Verify every row by md5** — hash-compare only, cheap, all tiers. *A row whose hash does not
   match halts work until reconciled* (D172/D188). A filename is not provenance (D188).
4. **Read into context only Tier 0:** the manifest, this START-HERE, the **KB Register**, the
   **HANDOFF_RUNBOOK**, and any **open incident**. Open **Tier 1** only when the task touches it.
   **Tier 2** is hash-verified but never read in the loop and never edited without a waiver (D34).
5. **Open `D:\Downloads\ClaudeCowork\00_INDEX.md`** — it says what is in the fourth store and which
   session kit rebuilds which work from raw data. **A session kit there is usually the shortest
   complete path into its subject**, and much cheaper than reading canon.
6. Then confirm, and ask which backlog item to start (**HANDOFF_RUNBOOK §2** = the live backlog).

---

## THE FOUR STORES, AND ONE RULE — read before writing anything anywhere

| store | authoritative for | must never hold |
|---|---|---|
| **project knowledge** | **canon** — Tier 0/1, everything the manifest names | bulk data, backups, superseded working papers |
| **GitHub** `drmanoj-clinic-automation` | **code**, plus `deploy_kits/KB_canon_all/` — the one folder `verify_live_pins.py` reads | patient data, secrets, **phone numbers (F-185)** |
| **`D:\Downloads\ClaudeCowork\`** | everything canon excludes; dated frozen snapshots; session kits | **any live, editable copy of a canonical document** |
| **external 1 TB SSD** — `F:\ClinicBackup\` | dated frozen mirrors of that folder, and the cold kits | nothing originates there — it is a copy, never a source |
| **Google Drive** | *not set up.* It was **never ruled out** — what was ruled out, measured, was putting canon in the **GitHub sync filter** (599% of the cap on its own). **Drive is still the only thing that would make this material readable from a phone**, because `D:` and `F:` are not | — |

**The one hard rule: no document may be live and editable in two stores** (D202 · F-201 — *neither
store is authoritative by position; compare by md5, never by where a file sits*). Frozen snapshots
are exempt: a cold backup is a copy by definition, and `KB_canon_all/` is a sanctioned second copy
the pin checker requires. Working papers are safe there because D351 rule three freezes them at
birth.

---

**Where the truth lives — read the manifest for the doc set and current versions; do not hard-code
them here:**

- **`CANONICAL_MANIFEST.md`** — the doc set, tiers, hashes. WINS on "what is canonical / current."
- **KB Register** (Tier 0) — what is true **NOW**: systems register, decisions index, live-file
  versions, backlog pointer.
- **KB History Archive** (Tier 1) — every session narrative and full decision text, **verbatim**.
  History only; opened on demand. **It lives in `deploy_kits/KB_canon_all/`, not in project
  knowledge** — it was moved out when the 2 MB cap came into view.
- **HANDOFF_RUNBOOK** (Tier 0) — §0 what happened last · §2 live backlog.
- **`OWNER_TODO_LIVE.md`** — the always-current owner list. Deliberately un-manifested.
- **Fault_Action_Register** (Tier 1) — the findings register (F-##).
- **SYSTEM_DOC_COVERAGE_MAP** — every subsystem → its authoritative doc.

> **No canonical document is a delta (D202, clarified by D247).** If a document arrives claiming to
> "carry forward vX unchanged," distrust it and verify against the manifest.

---

## PROJECT KNOWLEDGE IS CAPPED, AND EVERY CLOSE MOVES ONE TRANCHE OUT

The cap is **2 MB**. `KB_EXTENSION_PLAN` classifies **112 non-canonical documents** and gives the
order to retire them in; **step A13 of the close-out routine now moves one tranche per session**, or
says why it did not. Read the plan before moving anything — the classification matters more than the
count, and nine documents are marked **never move** however the manifest reads, including any
**incident not confirmed closed** (Phase 0 treats an open incident as Tier 0).

**Measure, never project.** At S206 a projection from file size said the Archive was 46.9 % of the
cap; the measured delta was **13.6 points** — wrong by more than three times, because
`knowledge_size` is an indexed measure and not a sum of bytes. **Report the measured figure before
and after.**

**The durable answer is branching Sanjeevni / Marg into its own project** once it is stable.
Tranches buy time; they are not the fix.

---

## THE BACKUP DISK — structure, cadence and retention

`F:\ClinicBackup\` is organised **one folder per project**, because it will hold more than this
one and a file loose at the root has no owner:

```
F:\ClinicBackup\
├─ 00_README_SSD_STRUCTURE.md
├─ DrManojClinic_Automation\
│   ├─ 01_KB_MIRRORS\      dated zips of D:\Downloads\ClaudeCowork      — every close
│   ├─ 02_COLD_KITS\       dated full handoff kits                      — see cadence below
│   ├─ 03_BUILD_BRIEFS\    the loose brief per close, readable unzipped — every close
│   └─ 99_SUPERSEDED\      older copies awaiting deletion
└─ _UNSORTED\              should always be empty
```

**COLD KIT CADENCE — take one when EITHER is true:** three sessions have passed since the last, **or
the KB Register or History Archive just bumped.** *(The bump usually comes first.)*

**Last taken: S207, 28-Aug-2026** — `DrManoj_Clinic_FULL_Handoff_Session207_2026-08-28.zip`,
94 files, md5 `8989e0f1d59b09379ecf322b421b7db2`, in `02_COLD_KITS\`.
**Next due: S210, or the next Register/Archive bump — whichever is first.**

**RETENTION — reviewed at every close.** Keep the 3 most recent mirrors and the 5 most recent cold
kits; move the rest to `99_SUPERSEDED\`. Keep **every** build brief — they are tiny and they are the
decision record. Sweep `__pycache__`, `.pyc` and duplicate raw exports.
**Moving is safe and the agent on manojz can do it; the final delete is the owner's.**
**Never remove the only copy of anything.**

**Connected sources:** Google Drive · Gmail · Notion ("Clinic HQ") · GitHub.
**ClickUp is parked (D17)** — do not check it or suggest it.

---
*START_HERE_PROMPT — v6 · supersedes v5 · adopted S207. This evergreen prompt is the
custom-instructions template; session-specific entry points (`START_HERE_SESSION_###`) are
regenerated at each close.*
