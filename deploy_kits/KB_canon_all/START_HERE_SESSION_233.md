# START HERE — SESSION 233

*Written at the S232 close, 08-Sep-2026. The evergreen template is `START_HERE_PROMPT_v8`; this is
the session entry point and it carries only what S233 needs.*

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
   documents, never in the conversation. **This was said again at S232 and it was earned.**
10. **English in chat and in his consoles, always.** Hindi is a staff-side requirement only.
11. **When a screen is wrong, read the screen's own code FIRST.** The server is the last suspect.
12. **Sub-agents read screens** — screenshots never enter the main conversation.

13. **⭐ NO CLAIM ABOUT WHAT EXISTS WITHOUT A READ IN THE SAME TURN — negative claims most of all.**
    *"there is no X"* / *"nothing is Y"* requires having looked for X, and saying where you looked.
    **Ruled at S232 after three wrong claims in one session, every one caught by the owner and not
    by me.** What gets BUILT goes through gates — selftests, hashes, prefix proofs, live-shape walks.
    What gets SAID about the estate went through nothing. **A negative claim is the dangerous class**,
    because he cannot check it without doing the work himself. If you have not looked, the honest
    answer is *"I don't know yet — let me check."*

**⭐ AND THE ONE FROM S232:** *"we need to stick to the core plan as much as possible and deviate only
for the compulsions."* **The plan is `claude/S232_ACTION_PLAN.md`. Adjacent good ideas are drift.**

---

## §1 · PHASE 0 — connections first, every time

**Check and name all three. Do not work around a missing store.**

| needed | what breaks without it |
|---|---|
| **`D:\Downloads`** | no Marg archive, no `_config`, **no ClaudeCowork** — the KB extension |
| **`D:\dr-manoj-git`** | no repository, no kits, no publish |
| **`F:\ClinicBackup`** | the close cannot mirror or take a cold kit |

⚠ **`D:\Downloads` has arrived unconnected at three consecutive opens (S229, S230, S232).** Expect
to request it by name. ⚠ **`F:` never mounts in the device shell and that is NOT unreachable** — the
file-transfer tools read and write it perfectly.

**Then verify the canon, from INSIDE its own folder:**

```
cd "$HOME/mnt/dr-manoj-git/drmanoj-clinic-automation/deploy_kits/KB_canon_all" && md5sum -c MD5SUMS_ALL.txt
```

**Expect 423 rows green, exit 0** *(413 at the S232 open; the close added ten)*. **Do not treat the
count as the expectation — `RESULT: PASS` is.** Halt on a hash MISMATCH; **a row absent from one
store is not a failed row.**

**Then the inverse check** — files on disk = rows listed + `MD5SUMS_ALL.txt` itself.

> ⭐ **AND THE S232 LESSON, which no gate will give you:** a green tells you the rows it HAS are
> true and **nothing about a row that is missing**. F-369 was four live VPS files that sat outside
> every pin list for three sessions under a green gate. **When you verify a set, ask what is not in
> it.**

**Read only Tier 0:** manifest · `START_HERE_PROMPT_v8` · KB Register **v5.82** · Runbook **v164** ·
`OWNER_TODO_LIVE.md`. Then open:

```
D:\Downloads\ClaudeCowork\00_INDEX.md
```

and the S232 papers in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S232\`.

---

## §2 · WHERE THINGS STAND

**Canon at this close:** Register **v5.82** · Archive **v1.79** · Fault **v2.64** · Runbook **v164** ·
manifest current · `live_pins_S232close.txt`.

**Next free: D429 · F-372 · Session 233.** *(**D428 is ruled and awaits minting**: the four
MyOperator Script-Property values for a restored DailyClinicReports go to **Bitwarden** — the owner's
word, 08-Sep, final. The stopgap file `D:\Downloads\margsync\_config\myop_defaults.json` retires
the moment they are filed.)*

**⚠ CORRECTED AFTER THIS FILE WAS FIRST WRITTEN.** Two claims of mine at the S232 close were wrong
and the owner caught both: *"the Apps Script projects and Sheets have no backup of any kind"* and
*"nothing in the backup chain is encrypted."* §3 below is the corrected version. The full measured
position is **`claude/S232_BACKUP_STATUS_CORRECTED.md`** — read it before starting §3.

**Three standing facts about this estate that must not be forgotten again:**

1. **The VPS state backup is AES-256 encrypted and ships to Drive nightly** (`clinic_state_backup.py`
   v2, S230, cron 01:50, September pinned forever). **Its restore has been drilled and passed** — the
   only leg here ever proven rather than assumed.
2. **Bitwarden is LIVE**, free tier, and already holds that bundle's encryption key (D415). The key
   is in three places: the VPS · `F:\ClinicBackup\S230_STATE_BACKUP\` (`clinic_state.key` 65 bytes
   + `READ_ME_KEY.txt` 1,427 bytes) · Bitwarden. **D421 defers only the bulk consolidation**, whose
   real subject is `D:\Downloads\Projects\_Infrastructure\Credentials\` — ten plaintext files.
   **The master password and 2FA recovery are on paper, deliberately outside Bitwarden.**
3. **Secrets never go to cloud storage.** That is a design rule of the shipper, not an omission.

**Genuinely blocked:** the WABA rotation, on **Ms. Khushi Jain's** answer — *do the old and new
tokens overlap?* **Nothing else in the plan waits on anything.**

**Held by the owner, both his rulings of 08-Sep:** the **PWA install** waits until the restructure
exercise is done · **Sanjeevni/Marg stays in this project** — develop it, then decide the split.

---

## §3 · WHAT S233 DOES — in the owner's order

**1 · Bring the Google plane into the backup chain that already works.** Not "build a backup" — the
chain exists and is proven; the Google plane was never brought inside it.

- **The seven live Sheets have no copy anywhere** — searched at S232 across the repo, `D:\Downloads\`
  and `D:\Downloads\ClaudeCowork\`. **They are the data, and they are the job.** They belong
  **inside the nightly encrypted Drive bundle** described in §2, whose restore has been drilled.
  **Do not invent a second mechanism.**
- **Six of the eight script projects holding real code ALREADY have a source copy**: `dashboard\`
  (14 files, verified against live at S230), the three in `deploy_kits\S230_GAS_EXPORT\`, and the
  Janitor and CC-saver files in `gmail-automation\gas\`. The two without a copy are both dead and
  both under the no-touch rule. **So the gap is not "no backup" — it is that nothing refreshes.**
  Build the **weekly re-export that diffs against the copy on disk**, so drift is reported instead of
  discovered.
- **Ten projects are named; an eleventh is only inferred** from an orphaned trigger the page cannot
  attribute. **Identify it before including it.**
- **Resolve the `VPS_Push_UPI.gs` duplicate** — the repo holds a 200-line copy and the live 263-line
  one. That is the D202/F-201 breach we forbid everywhere else.

**D426 put Drive reads and writes in scope**, so this can run unattended.
`claude/S232_APPS_SCRIPT_TRIGGERS_READ.md` says which projects are actually armed.

**2 · Sanjeevni steps 2+3, clubbed** — derivation off the screens, lanes pointed at the spine.
**The spine was built at S229 and nothing reads it.** No screen changes behaviour.

**3 · Step 4 — sections as jobs**, with him, screen by screen. **He asked to be part of this one.**

**Do not start 2 before 1, and do not start anything else before either.**

---

## §4 · THREE THINGS THAT WILL BITE IF FORGOTTEN

1. **The F-368 quarantine folder must NOT be deleted until after the WABA rotation** —
   `/root/_quarantine_S232_F368_20260908_111131/` still holds the old token, and it is the record of
   what was public.
2. **`deploy_kits/S232_F370_COMMENT/staff_ledger.py` is the NEW BASE** for the next kit touching that
   file. The live pin `80257711…` has not moved; do not start from the S225 copy.
3. **Never run `git` against the mounted repo (F-233)** — and `GIT_OPTIONAL_LOCKS=0` does **not**
   avoid it, measured at S232. If you must, rename `.git\index.lock` aside immediately and say so.

---

## §5 · THE PERSONAL GOOGLE PLANE — added mid-S233, and it CARRIES FORWARD

**Read `PERSONAL_GOOGLE_PLANE_v1_S233.md` before touching anything in the owner's PERSONAL Google
account, or designing anything that writes the Payment Register or the renewals.** Four facts, all
read from exported source on 08-Sep-2026, each of which would otherwise be rediscovered the hard way:

1. **The renewals ALREADY push to the VPS daily** — `/finance/api/renewals-push`, on every run, quiet
   days included. **Do not build that again.**
2. **The Payment Register is CREATED and appended BY the Janitor**, its id in a Script Property. A VPS
   table must read it as an upstream source, never co-author it.
3. **The bank chain has a FOURTH limb** — `Bank_Statement_Relay.gs` forwards statement mail personal →
   clinic daily at 07:00. It is inside the *read, never act* hold.
4. **A third personal book, `PERSONAL_DOCS_ID`, has no backup and appears in no census.**

🛑 **The two project exports and their books NEVER go into git** — passports, licences, an arms-licence
UIN, policy numbers, and a `govt ID` tab. They live in
`D:\Downloads\ClaudeCowork\04_SOURCE_DATA\S233_GOOGLE_EXPORTS_2026-09-08\` and
`F:\ClinicBackup\S233_GOOGLE_EXPORTS_2026-09-08\`. Permanent.

**This section must be carried into every later entry point.**

---
*START_HERE_SESSION_233 · written at the S232 close, 08-Sep-2026 · §5 added mid-session, 08-Sep.*
