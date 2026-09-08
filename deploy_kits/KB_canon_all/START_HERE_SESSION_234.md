# START HERE — SESSION 234

*Written at the S233 close, 08-Sep-2026. The evergreen template is `START_HERE_PROMPT_v8`; this is
the session entry point. **S234 starts in a FRESH CHAT — nothing from S233's conversation carries.
This file and the documents it names are the whole handover.***

---

## §0 · THE STANDING OWNER RULINGS — read before working

1. **Publishing is HIS double-click.** Name ONE file, full path. Never publish for him.
2. **Full paths ALWAYS — including URLs**, each in its own copy block. Never a bare `/finance/...`.
3. **ONE line per command.** A multi-line paste has twice been cut in transit.
4. **Plain language. One step at a time. Full-file replacements. ALL-CAPS from him = urgent.**
5. **Mask patient numbers (last 4). Never print a secret or a token.**
6. **Nothing live is rebuilt without his OK; the manual path stays as fallback.**
7. **Do not hand him diagnostics, investigations or A/B tests.** Do the background work; ask for the
   one action nobody else can do — a GUI step, a credential, a decision — **in one line.**
8. **Do not put technical or architectural choices to him.** *"I don't grasp these and cannot answer
   them the way you expect."* Make the call, state it in one line, proceed. He weighs in on what he
   can SEE: a screen, a wording, a workflow, a priority.
9. **Keep chat SHORT.** *"less for me to read, its your turf."* Long write-ups go in project
   documents, never in the conversation.
10. **English in chat and in his consoles, always.** Hindi is a staff-side requirement only.
11. **When a screen is wrong, read the screen's own code FIRST.** The server is the last suspect.
12. **Sub-agents read screens** — screenshots never enter the main conversation.
13. **⭐ NO CLAIM ABOUT WHAT EXISTS WITHOUT A READ IN THE SAME TURN — negative claims most of all.**
    Ruled at S232 after three wrong claims in one session. **S233 proved the rule twice more**: a
    canonical README described the hash gate wrongly and nearly narrowed it (F-374), and *"the
    Callback Tracker is one spreadsheet"* was too narrow and he doubted it correctly.
14. **⭐ NEW, S233 — HIS CHALLENGE TO A PLAN IS DATA, NOT AN OBJECTION TO ANSWER.** He challenged the
    S233 plan five times and **was right five times**, once fatally: the plan's headline claim did
    not survive one `device_list_dir`. **When he questions the premise, go and measure before
    defending.** The measurement is usually one call and it is usually his way.
15. **⭐ NEW, S233 — THE SENSITIVITY QUESTION IS CLOSED FOR THE VPS (D429).** *"VPS is owned by me and
    I feel it's a safe place to keep on the data."* **Do not raise it again.**
16. **Stick to the core plan.** Adjacent good ideas are drift.

---

## §1 · PHASE 0 — connections first, every time

**Report what is connected, ask for what is missing BY NAME, work around nothing.**

| needed | what breaks without it |
|---|---|
| **`D:\Downloads`** | no Marg archive, no `_config`, **no ClaudeCowork** — the KB extension |
| **`D:\dr-manoj-git`** | no repository, no kits, no publish |
| **`F:\ClinicBackup`** | the close cannot mirror or take a cold kit |
| the assistant's browser | no live-page reads (still in the F-242 login loop) |

⚠ **`D:\Downloads` has NOT been connected at the open for three sessions running** (S229, S232,
S233). Expect to ask for it. ⚠ **`F:` never mounts in the device shell and that does NOT mean
unreachable** — the file-transfer tools read and write it perfectly.

**Then:** `CANONICAL_MANIFEST.md` → **verify every row by md5 from INSIDE `deploy_kits/KB_canon_all/`**
→ read only Tier 0 → open `D:\Downloads\ClaudeCowork\00_INDEX.md` and the latest build brief.

**At the S233 close the gate stood at 429 rows, exit 0.**

⚠ **F-374, minted this close: `README_VERIFY.md` used to describe that gate wrongly and rebuilding
to its description dropped a row silently. When you rebuild `MD5SUMS_ALL.txt`, DIFF THE NEW ROW LIST
AGAINST THE OLD AND PROVE NOTHING WAS DROPPED.** A gate that loses a row still exits 0.

---

## §2 · WHERE THINGS STAND

**Live and new at S233 — the Google Sheets ride the nightly bundle.** `sheets_pull.py`
`09b08eae…` (cron 01:45) writes four books to CSV under `/root/state_backup/sheets/`;
`clinic_state_backup.py` v3 `fba57985…` carries that directory inside the AES-256 bundle at 01:50.
First run: **35,030 rows** — tracker 19 tabs / 21,157 · audit 4 / 13,585 · renewals 2 / 37 ·
payment_register 1 / 251.

**Three standing estate facts:**

- The **nightly encrypted Drive backup** has run since S230, restore drilled and passed, key in
  three places (VPS · `F:\ClinicBackup\S230_STATE_BACKUP\` · Bitwarden, D415).
- **Bitwarden is LIVE, not pending.** D421 defers only the bulk consolidation.
- **Secrets never go to cloud storage.**

**🔴 AND THE ONE THAT MATTERS MOST, MEASURED AT S233 AND STILL TRUE:**
`F:\ClinicBackup\S230_STATE_BACKUP\` holds `clinic_state.key` (65 bytes) and **no bundle**;
`ColdBackups\` holds no state bundle either. **So the encrypted nightly bundle exists in exactly one
place — Google Drive.** For VPS data that is a real second home; for anything already in Google the
chain is Google → VPS → Google and never leaves the account. **It cannot be a nightly job — his PCs
are off at night — so it must be a catch-up copy that runs when a machine is awake.**
**He DEFERRED this on 08-Sep. Do not start it without asking him.**

**🛑 Blocked on one answer:** Ms. Khushi Jain / MyOperator — **do the old and new WABA tokens
overlap?** The only thing still blocking anything.

---

## §3 · WHAT S234 DOES — his order, D432, in his own words

> *"start next session by completing detour, followed by sanjeevni work"*

**FIRST — finish the detour, in this order:**

1. **The Payment Register as a real table** on the VPS, for the payments product. ⚠ **Read
   `PERSONAL_GOOGLE_PLANE_v1_S233.md` first:** the register is **created and appended BY the
   Janitor**, its id in a Script Property. A VPS table must read it as an **upstream source** and
   never co-author it, or the two diverge silently.
2. **The third personal book** — `PERSONAL_DOCS_ID`, identity-document rows, **no backup and in no
   census**. Small.
3. **Reconcile the two renewal registers** — the Janitor's own array (~two dozen entries, and the
   one the nag and the VPS push both read) against `Renewals_And_Vendor_Register_v1_S232`. Neither
   derives from the other; they will drift.
4. **The weekly script re-export that diffs against the copy on disk.** Every script copy is a
   one-off snapshot that goes stale the first time someone edits in the browser, and nothing says so.
5. **The orphaned trigger's project** · **the `VPS_Push_UPI.gs` duplicate** (D202/F-201).

**THEN — Sanjeevni steps 2+3, clubbed.** Derivation off the screens, the four lanes pointed at the
spine. **The spine was built at S229 and nothing reads it yet.** Every derived number carries its
coverage **as data, not as a sentence**. No screen changes behaviour. Then step 4, sections as jobs,
screen by screen **with him — he asked to be part of it.**

**Still not started, and the origin of all of it:** the VPS clean-up and the sensitivity system.

---

## §4 · THE PERSONAL GOOGLE PLANE — carried forward from S233, and it must keep being carried

**Read `PERSONAL_GOOGLE_PLANE_v1_S233.md` before touching anything in his PERSONAL Google account or
designing anything that writes the Payment Register or the renewals.** Four facts, each read from
exported source on 08-Sep-2026:

1. **The renewals ALREADY push to the VPS daily** — `Renewal_Nag.gs` POSTs to
   `/finance/api/renewals-push` on every run, quiet days included. **Do not build that again.**
2. **The Payment Register is CREATED and appended BY the Janitor.**
3. **The ICICI → VPS bank chain has a FOURTH limb** — `Bank_Statement_Relay.gs`, personal → clinic
   at 07:00 daily. Inside the *read, never act* hold.
4. **A third personal book, `PERSONAL_DOCS_ID`, has no backup and appears in no census.**

🛑 **D431 — the two project exports and their books NEVER enter git.** Passports, licences, an
arms-licence UIN, policy numbers, a `govt ID` tab. They live in
`D:\Downloads\ClaudeCowork\04_SOURCE_DATA\S233_GOOGLE_EXPORTS_2026-09-08\` and
`F:\ClinicBackup\S233_GOOGLE_EXPORTS_2026-09-08\`. **Permanent.**

**Carry this section into every later entry point.**

---

## §5 · STANDING HOLDS

- **Apps Script: read, never act.** The ICICI → VPS bank chain is load-bearing across **four**
  limbs now. **The Clinic Callback Tracker is not to be touched at all**, nor its dead ancestor,
  which carries an unscoped `removeTriggers()`.
- **The PWA install waits** until this exercise is done. **Sanjeevni/Marg stays in this project**
  for now. **NEFT: nothing is sent without his word.**
- **The call recordings** — mp3s in a new Drive folder every month, a few MB a day, under a GB a
  year, **no copy outside Google Drive.** The largest unprotected thing in the estate. **His
  decision, not started.**

---

## §6 · FIVE THINGS THAT WILL BITE IF FORGOTTEN

1. **`py_compile` ALWAYS writes a `.pyc`** — `python -B` does not stop it, because writing the
   bytecode is the function's purpose. The `__pycache__` is `.gitignore`d and **the publish gate
   refuses the publish** (F-376, and it happened at S233). Compile with
   `py_compile.compile(f, cfile='/tmp/chk.pyc', doraise=True)`.
2. **A one-line installer that lives in the deploy clone cannot pull the clone that fetches it**
   (F-375). **The install is two lines: the deploy pull, then the installer.**
3. **Never run `git` against the mounted repo (F-233)** — and `GIT_OPTIONAL_LOCKS=0` does not avoid
   it. Rename `.git\index.lock` aside immediately and say so.
4. **The F-368 quarantine folder must NOT be deleted until after the WABA rotation** —
   `/root/_quarantine_S232_F368_20260908_111131/`.
5. **`deploy_kits/S232_F370_COMMENT/staff_ledger.py` is the NEW BASE** for the next kit on that file.

---

## §7 · NEXT FREE NUMBERS

**D433 · F-377 · Session 234.** Canon at the S233 close: Archive **v1.80** · Register **v5.83** ·
Fault **v2.65** · Runbook **v165** · `live_pins_S233close.txt` · manifest gate **429 rows, exit 0**.

---
*START_HERE_SESSION_234 · written at the S233 close, 08-Sep-2026. S234 begins in a fresh chat: this
file is the handover.*
