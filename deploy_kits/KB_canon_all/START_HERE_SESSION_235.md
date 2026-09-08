# START HERE — SESSION 235

*Written at the S234 close, 08-Sep-2026. The evergreen template is `START_HERE_PROMPT_v8`; this is
the session entry point. **S235 starts in a FRESH CHAT — nothing from S234's conversation carries.
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
   them the way you expect."* Make the call, state it in one line, proceed.
9. **Keep chat SHORT.** *"less for me to read, its your turf."* Long write-ups go in project
   documents, never in the conversation.
10. **English in chat and in his consoles, always.** Hindi is a staff-side requirement only.
11. **When a screen is wrong, read the screen's own code FIRST.** The server is the last suspect.
12. **Sub-agents read screens** — screenshots never enter the main conversation.
13. **⭐ NO CLAIM ABOUT WHAT EXISTS WITHOUT A READ IN THE SAME TURN — negative claims most of all.**
14. **⭐ HIS CHALLENGE TO A PLAN IS DATA, NOT AN OBJECTION TO ANSWER.** S233: five challenges, five
    times right. **S234 made it seven** — the `dr-manoj.in` auto-renew that had never been set, and
    Bhawna's licence expiry, which was already in his own `govt ID` tab.
15. **⭐ NEW, S234 — SEARCH THE WHOLE OF WHAT HE ALREADY HAS BEFORE ASKING HIM FOR ANYTHING.** At
    S234 he was asked for a date he had been keeping for months. His standing words: *"all is in
    project kb, you can confirm, and shd confirm on your own before these erratic answers."*
16. **THE SENSITIVITY QUESTION IS CLOSED FOR THE VPS (D429).** *"VPS is owned by me and I feel it's
    a safe place to keep on the data."* **Do not raise it again.**
17. **Stick to the core plan.** Adjacent good ideas are drift.

---

## §1 · PHASE 0 — connections first, every time

**Report what is connected, ask for what is missing BY NAME, work around nothing.**

| needed | what breaks without it |
|---|---|
| **`D:\Downloads`** | no Marg archive, no `_config`, **no ClaudeCowork** — the KB extension |
| **`D:\dr-manoj-git`** | no repository, no kits, no publish |
| **`F:\ClinicBackup`** | the close cannot mirror or take a cold kit |
| the assistant's browser | no live-page reads (still in the F-242 login loop) |

⚠ **`D:\Downloads` has NOT been connected at the open for FOUR sessions running** (S229, S232, S233,
S234). Expect to ask for it; it is granted immediately when named.
⚠ **`F:` never mounts in the device shell and that does NOT mean unreachable** — the file-transfer
tools read and write it perfectly.

**Then:** `CANONICAL_MANIFEST.md` → **verify every row by md5 from INSIDE
`deploy_kits/KB_canon_all/`** → read only Tier 0 → open `D:\Downloads\ClaudeCowork\00_INDEX.md` and
the latest build brief.

**At the S234 close the gate stood at 443 rows, exit 0 — MEASURED, not projected.** *(435 at the
S234 open; 436 when `deploy/push_kit.bat` was brought inside it; 443 after the close added seven
rows — the new Archive, Register, Fault Register, Runbook, entry point, pin file and the manifest's
dated backup. **Added seven, dropped none, two hashes changed** — the manifest and `KIT_ID.txt`.)*

⚠ **F-374 still governs every rebuild of `MD5SUMS_ALL.txt`: rebuild from the PREVIOUS ROW LIST and
DIFF IT.** A gate that quietly loses a row still exits 0.

---

## §2 · WHERE THINGS STAND

**Live and new at S234 — the detour closed whole:**

- **`/root/finance/payments_register.py` `fa12a0a1…`** · cron 02:05 · **250 rows**. The Payment
  Register as a real table in `finance.db`, read one-way from the 01:45 pull's CSV. **D433: it reads
  the sheet as an upstream source and can never write back.**
- **`/root/state_backup/gas_export.py` `072a9411…`** · cron **Sunday 02:20** · 3 projects. Weekly
  Apps Script re-export, comparing against last week AND against the repository copy. **D434: the
  Callback Tracker is denylisted in code — EXIT 44 before any network call.**
- **A fifth book in the nightly pull** — `personal_docs`, the identity-document sheet. 5 books,
  10 rows, inside the encrypted bundle.

**Three standing estate facts, unchanged:**

- The **nightly encrypted Drive backup** has run since S230; restore drilled and passed; key in three
  places (VPS · `F:\ClinicBackup\S230_STATE_BACKUP\` · Bitwarden, D415).
- **Bitwarden is LIVE, not pending.** D421 defers only the bulk consolidation.
- **Secrets never go to cloud storage.**

**🔴 AND THE ONE THAT MATTERS MOST, MEASURED AT S233 AND STILL TRUE:** the encrypted nightly bundle
exists in **exactly one place — Google Drive**. `F:\ClinicBackup\S230_STATE_BACKUP\` holds the key
and no bundle. **He DEFERRED this on 08-Sep. Do not start it without asking him.**

**🛑 Blocked on one answer:** Ms. Khushi Jain / MyOperator — **do the old and new WABA tokens
overlap?**

---

## §3 · WHAT S235 DOES

**Sanjeevni steps 2+3, clubbed** — D432's own next step. Derivation off the screens; the four lanes
pointed at the **item spine built at S229 that nothing reads yet**. Every derived number carries its
**coverage as data, not as a sentence**. **No screen changes behaviour.**

Then **step 4 — sections as jobs**, screen by screen, **with him — he asked to be part of it.** Six
role maps (`S230_SURFACE_AND_ROLES` §6), not forty-two tiles.

**Read first:** `S235_BUILD_BRIEF.md`, then `S229_ITEM_SPINE_BUILT.md` and
`S229_SANJEEVNI_ARCHITECTURE_TAKE.md`.

**Still not started, and the origin of all of it:** the VPS clean-up and the sensitivity system.

---

## §4 · THE PERSONAL GOOGLE PLANE — carry this section into every later entry point

**Read `PERSONAL_GOOGLE_PLANE_v1_S233.md` before touching anything in his PERSONAL Google account.**

1. **The renewals ALREADY push to the VPS daily** — `Renewal_Nag.gs` POSTs to
   `/finance/api/renewals-push` on every run. **Do not build that again.** Measured at S234: the push
   sends only items inside **35 days forward / 45 overdue**, so of 23 dated entries **exactly one**
   reaches the health card today. It is a near-term card, not the register.
2. **The Payment Register is CREATED and appended BY the Janitor** — and **F-377**: the sheet has
   silently re-dated **95 of its own 250 rows**, because Google reads appended day-first strings
   month-first. The VPS table is correct because it reads *displayed* values day-first; **sorting
   that sheet by date inside Google sorts 95 rows wrongly.**
3. **The ICICI → VPS bank chain has a FOURTH limb** — `Bank_Statement_Relay.gs`, personal → clinic
   at 07:00 daily. Inside the *read, never act* hold.
4. **`Renewals_And_Vendor_Register_v2_S234` is the current register**, and v1 is superseded. The
   Janitor's own array remains **the operative one** — advancing a date there is what silences a nag.

🛑 **D431 — the two personal project exports and their books NEVER enter git.** They live in
`D:\Downloads\ClaudeCowork\04_SOURCE_DATA\S233_GOOGLE_EXPORTS_2026-09-08\` and
`F:\ClinicBackup\S233_GOOGLE_EXPORTS_2026-09-08\`. **Permanent.**

---

## §5 · STANDING HOLDS

- **Apps Script: read, never act.** The ICICI → VPS bank chain is load-bearing across **four** limbs.
  **The Clinic Callback Tracker is not to be touched at all** — and from S234 that hold is enforced
  **in code**, not only in prose (D434).
- **Two array edits are OWED and deliberately not made** (`Renewals_And_Vendor_Register_v2_S234` §6):
  the `dr-manoj.in` note, which still describes an auto-renew set in Aug-2026 when it was set on
  08-Sep-2026 onto card ·9012; and Bhawna's DL entry, whose date is now known — **09-Jan-2030**.
- **PARKED BY HIM at the S234 close:** three date inconsistencies in the `govt ID` tab. *"Park for
  later so that one source of truth gets populated everywhere."* **Do not fix these piecemeal.**
- **The PWA install waits.** **Sanjeevni/Marg stays in this project** for now. **NEFT: nothing is
  sent without his word.**
- **The call recordings** — no copy outside Google Drive. **His decision, not started.**

---

## §6 · SIX THINGS THAT WILL BITE IF FORGOTTEN

1. **`py_compile` ALWAYS writes a `.pyc`** — `-B` does not stop it. Compile with
   `py_compile.compile(f, cfile='/tmp/chk.pyc', doraise=True)` (F-376).
2. **The install is TWO lines** — the deploy pull, then the installer (F-375).
3. **Never run `git` against the mounted repo (F-233).** `rm` and `rmdir` are refused there by
   design: move aside and say so, never work around it silently.
4. **The F-368 quarantine folder must NOT be deleted until after the WABA rotation** —
   `/root/_quarantine_S232_F368_20260908_111131/`.
5. **`deploy_kits/S232_F370_COMMENT/staff_ledger.py` is the NEW BASE** for the next kit on that file.
6. **The publish gate's `.gitignore` check is scoped to `deploy_kits · logo · canonical-docs`** —
   read from `PUBLISH_ALL.bat` at S234, not assumed.

---

## §7 · NEXT FREE NUMBERS

**D437 · F-379 · Session 235.** Canon at the S234 close: Archive **v1.81** · Register **v5.84** ·
Fault **v2.66** · Runbook **v166** · `live_pins_S234close.txt` · manifest gate **443 rows, exit 0**.

---
*START_HERE_SESSION_235 · written at the S234 close, 08-Sep-2026. S235 begins in a fresh chat: this
file is the handover.*
