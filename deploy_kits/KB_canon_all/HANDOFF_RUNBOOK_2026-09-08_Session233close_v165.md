# HANDOFF RUNBOOK — v165 · S233 close · 08-Sep-2026

*Supersedes v164. Tier 0. §2 is the live backlog.*

---

## §0 · WHAT HAPPENED

**One session, opened on ⭐1-1 and closed on a plan the owner rewrote from underneath it.**

`S233_SHEETS_BACKUP` was built, walked and installed: `sheets_pull.py` writes each configured
Google Sheet to one CSV per tab under `/root/state_backup/sheets/`, and `clinic_state_backup.py`
**v3** — the S230 file with **one row added to `SRC_DIRS`** — carries that directory inside the
AES-256 bundle that has gone to Drive nightly since S230. **No second key, no second destination, no
second mechanism.** Live from one line at ~17:00 IST: four books, **35,030 rows**, cron 01:45, both
pins predicted offline and read back from the box identical.

**Then the owner asked the question the session should have asked itself** — *"do we really need to
pull all the data from Google Drive, while it is sitting there well secure ... what should be the
reason to load the VPS with this data?"* — **and he was right five times.**

He was right that three of the eight books were the dead Google-Forms system, already unmonitored.
He was right that a fourth, `patient_diagnosis`, was **already** being read into `console.db`. He was
right that Google's own version history beats a nightly CSV for the accident case. He was right that
**a nightly copy to `F:` cannot work when the PCs are off at night**. And the fifth ended the
argument: `F:\ClinicBackup\S230_STATE_BACKUP\` holds the key and **no bundle**, so **the encrypted
nightly bundle exists in exactly one place — Google Drive** — and the plan did not protect against
the one failure Google cannot cover. **Eight books became four.**

He then exported both personal Apps Script projects and both of their books — **the only complete
copies that exist** — and reading them mapped a plane this project had never seen: the renewals
already push to the VPS daily, the Payment Register is created and written by the Janitor itself, the
bank chain has a fourth limb running personal → clinic, and a third personal book has no backup at
all. All four are now canon, in a document **and** in §5 of the entry point, because a document alone
can sit unopened.

**Five findings, all five the assistant's own** (F-372 … F-376), two of them caught by the owner's
own gates rather than by any check of mine.

---

## §1 · THE MENTAL MODELS — six, five of them new

1. **⭐ WHEN HE CHALLENGES THE PREMISE, MEASURE — DO NOT DEFEND.** He challenged five times and was
   right five times. The fifth took **one `device_list_dir` call** to settle, and it retracted the
   plan's headline claim. The cost of measuring is one tool call; the cost of defending is shipping
   a backup that does not back anything up.
2. **⭐ A COPY IN THE SAME ACCOUNT IS NOT A SECOND COPY.** Google → VPS → Google protects against a
   bad script, which Google already protects against better. It does not protect against losing the
   account, which is the only failure Google cannot cover. **Ask what failure a backup is FOR
   before choosing where it lands.**
3. **⭐ A GATE DESCRIBED IN PROSE IS NOT THE GATE.** `README_VERIFY.md` said the checksum file
   excludes two files; it excludes one, and rebuilding to that description dropped a row — silently,
   exit 0 (F-374). **Rebuild from the previous row list and diff, never from a description.** This is
   F-369's shape three sessions later, in the document that exists to prevent it.
4. **⭐ ONE MESSAGE FOR EVERY FAILURE IS A MESSAGE THAT LIES.** A quota refusal wearing a sharing
   refusal's words would have sent him to Google to re-share five sheets that were already correct
   (F-373). **Give each failure class its own exit code and its own words, and put a test on the
   words** — walk check 28 asserts a rate refusal never contains "share".
5. **⭐ DERIVED IS NOT BACKED UP — CHECK WHICH WAY THE DATA FLOWS.** `console.db` is **rebuilt** from
   the Call Audit sheet. Backing up the database preserves nothing; the sheet is the original and
   13,585 verdict rows depend on it. *He asked whether that sheet had any practical use: he never
   needs to open it, and it must still be backed up. Both answers are true.*
6. **The one-line handover has to be able to run.** The installer lived inside the clone it pulls
   (F-375). **A one-line entry point is two lines if the first line is what fetches it.**

---

## §2 · THE LIVE BACKLOG — his order, D432

**⭐0 · NEEDS HIM:** the MyOperator overlap answer (still the only blocker) · four values into
Bitwarden (D428) · Amir's renames · the VINTAZ tap · the August advances · the delete lists · **and
one decision: the call recordings**, no copy outside Google Drive.

**⭐1 · FINISH THE DETOUR, then Sanjeevni** — *"start next session by completing detour, followed by
sanjeevni work"*:

1. **Payment Register as a real table** — read `PERSONAL_GOOGLE_PLANE_v1_S233` first; the Janitor
   writes that sheet and the VPS must not co-author it.
2. **The third personal book** (`PERSONAL_DOCS_ID`) — no backup, in no census.
3. **The two renewal registers reconciled** before they drift.
4. **The weekly script re-export** that diffs against disk.
5. **The orphaned trigger's project** · the **`VPS_Push_UPI.gs` duplicate**.

**THEN Sanjeevni steps 2+3, clubbed** — the spine was built at S229 and nothing reads it. Then step
4, sections as jobs, with him.

**DEFERRED BY HIM:** getting the bundle out of Google · raw vehicle tracker into the VPS · retiring
the email side of the legacy scripts · documenting the live Apps Script projects.

**Never started, and the origin of all of it:** the VPS clean-up and the sensitivity system.

---

## §3 · INSTALL DISCIPLINE — what S233 adds

- **Compile without leaving a `.pyc`.** `py_compile` always writes one and `-B` does not stop it;
  the `__pycache__` is `.gitignore`d and **his publish gate refuses the publish** (F-376).
- **A self-gating installer beats a numbered list, and it must fail safe.** `install.sh` runs nine
  stages, proves each before the next, keeps a dated copy of both live scripts, deletes nothing but
  exported copies whose source is still in Google, and **switches the schedule on only after proving
  the sheets readable, the pull good and the bundle actually containing them.** On **every** failure
  path the schedule stays off. `WALK_install.py` makes it fail in each of those ways — 24 checks.
- **Walk the seam, not just the halves.** `WALK_clinic_state.py` replaces `SRC_DIRS` with its own
  fixtures, so its 104 checks never looked at the row S233 added. `WALK_v3_seam.py` runs the real
  exporter, takes its real bytes, and points the real `gather()` at them.
- **Make the guard fail on purpose.** Checks 8–9 wipe a tab and read the survivors back; 30–33 make
  Google refuse twice, then permanently.
- **Kit total: 71 checks across four walks.**

---

## §4 · THE BOUNDARY — what is true, and what is only believed

**True, read this session:** the four books are on the box and in the bundle (row counts and both
pins read back from the box) · the bundle exists only in Google Drive (`F:` listed) · `console.db`
is rebuilt from the audit sheet (source read) · the renewals already push to the VPS (source read) ·
no clinic-account twin of the personal projects (searched) · the gate stands at 429 rows, exit 0,
one row added and none dropped (diffed).

**Believed, not proven:** the size of the recording archive — **estimated from a ten-file sample on
one day**, not measured. Say so if it is quoted.

**Owed:** `KIT_ID.txt` in `KB_canon_all` still reads **S226 close** with S226-era versions — stale by
seven sessions, in the folder's own identity card, and the file itself records having gone stale
once before. **Not fixed at this close; carried to S234.** So is the `push_kit.bat`-inside-canon-
outside-the-gate question, which has now been carried twice.

---
*HANDOFF_RUNBOOK v165 · S233 close · 08-Sep-2026. Next free: **D433 · F-377 · Session 234**.*
