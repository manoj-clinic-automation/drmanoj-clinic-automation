# END OF SESSION — full session close-out (v16) · SELF-CONTAINED

**Say "EOS"** (build session: code/config changed) **or "EOS-light"** (fold-in / documentation /
planning: no live code touched). EOS-light skips only **C** (GitHub commit) and **B's** Gmail
health note. Everything else runs identically. If the mode is unclear, ask once rather than guess.

---

## ⭐ WHAT v16 ADDS — S269, 18-Sep-2026 (everything else is v15, whole)

Seven rules, every one of them earned on 17 or 18 September, each written where its step lives:

1. **THE NIGHTLY BUNDLE IS 01:35 EVIDENCE AND NOTHING LATER (S269).** "The bundle does not show it"
   proves only *not before 01:35* — never *not done*. At S269 the assistant read the 18-Sep bundle,
   saw an unchanged legs file, and told the owner a published kit had never been installed. It had
   been installed that morning, after the bundle was taken. **Before convicting from the bundle,
   ask the live surface — the read-only check the kit itself offers.** (A0.)
2. **A URL HANDED TO THE OWNER IS A LIVE ROUTE, OR IT IS NOT PRINTED (S269).** A kit's closing line
   sent him to `/finance/freshness`, which 404s and always has: the collector writes a **file**, and
   nothing serves it. Check a URL against the app's own routes before it reaches a kit, a message or
   canon. (A0, A16.)
3. **LIST `KB_canon_all\` IMMEDIATELY BEFORE WRITING CANON (F-534).** The other project's close may
   have landed minutes ago; append onto the versions that are *there*, not the ones read at the open.
   (A1, A7.)
4. **THE PIN CHECK STATES ITS PENDING COUNT (F-513).** A DECLARED-PENDING pin is a promise to read
   back at the next open; a promise older than one close is a finding at every close until it is
   kept. State the count beside the three counts. (A8, A11b, A17 row 17.)
5. **CLAIM THE KIT NUMBER BEFORE THE SCRATCH FOLDER IS NAMED (F-515).** Two open chats built two
   kits under one number because the board claim was written after the folder. (A11c.)
6. **A KIT THAT CARRIES A BLANKET-IGNORED FILE TYPE NEEDS ITS ALLOW LINE IN THE SAME BREATH
   (F-300 family).** `.gitignore` blocks `*.json` wholesale; `PUBLISH_ALL.bat` refuses the whole run
   with *"at least one file was silently excluded by .gitignore"* and commits nothing. Add the
   exact-path `!deploy_kits/S###_NAME/file.json` line when the kit is copied in, and state it in the
   close report. (A11c, A16, A17 row 18.)
7. **THE BOARD'S SANJEEVNI PLAN IS REFRESHED BY EVERY CLOSE (D534).** (A10c, A17 row 16.)

**Lineage:** v16 S269 · v15 S263 · v14 S258 · v13 S209 · v12 S209 · v11 S208 · v10 S207 · v9 S206 ·
v7 S201 · v6 S194 · v5 S188 · v4 D247.

---

## ⭐ WHAT v15 ADDS — S263, 17-Sep-2026 (everything else is v14, whole)

Four rules, each earned on 17-Sep, each written where its step lives:

1. **A clock time is READ, never estimated (F-510).** Every time written into canon comes from `date`, a
   commit stamp in `.git/logs/HEAD`, a file mtime, or a line a program printed — at the moment of writing.
   (A0, A16b.)
2. **No git command in `device_bash` against a connected folder — ever (F-511).** The shell can create
   files there but cannot unlink them, so git leaves `.lock` files that make the owner's publish refuse.
   Read the repository's files instead. (A16, A16b.)
3. **A kit is built in scratch and copied into `deploy_kits/` only when final and gated; once it could have
   been published it is frozen, and a change to it is a new kit (F-512).** (A11c.)
4. **The System Board's page is refreshed by every close, in whichever project closes (D533).** (A10c,
   A17 row 16.)

**Lineage:** v15 S263 · v14 S258 · v13 S209 · v12 S209 · v11 S208 · v10 S207 · v9 S206 · v7 S201 · v6 S194 ·
v5 S188 · v4 D247.

---

## ⚠ WHY v14 EXISTS — S258, 15-Sep-2026

Four steps of this routine are now done by a machine every night at 03:10, and one more can be.
v14 changes what the close **does** about them: it stops performing them and starts **verifying**
them.

> **THE RULE THAT MAKES THAT SAFE, AND IT IS NOT OPTIONAL:**
> **a step the nightly owns is VERIFIED at the close, never assumed.**
> **A missing report, a stale report, or a report with a non-zero verdict is a RED — and the close
> then performs that step by hand, exactly as v13 did.**
>
> Automation removes the *labour* of a step. It never removes the *check*. A close that reads
> "the nightly does that now" and looks no further has replaced one unread step with another.

**Why v13 needed changing.** It told the close to rebuild the Cowork manifest, take the SSD mirror
and re-run `MD5SUMS_ALL` by hand. All three had been *owed* at closes rather than done — the mirror
was owed from 8-Sep, the manifest rebuild from 8-Sep, and `MD5SUMS_ALL` silently stopped covering
two files without any close noticing. **A step that has to be remembered is a step that stops.**

**What v13 got right and v14 keeps whole:** A0's evidence rule, every hash-and-prove instruction,
A17's *silence is never DONE*, and the self-contained principle — **if a step is not written in
this file, it is not part of the close.**

**Lineage:** v13 S209 (self-contained by owner ruling) · v12 S209 (A16) · v11 S208 (A14, A15) ·
v10 S207 · v9 S206 · v7 S201 · v6 S194 · v5 S188 · v4 D247.

---

# A0 · THE EVIDENCE RULE — read before any comparison in this close

**RE-KEYED TEXT MAY CORROBORATE. IT MAY NEVER CONVICT.** Any claim that two copies differ must rest
on bytes handled as bytes — hashed, diffed, or delivered as a file — or on two independent
transcriptions that agree. *At S204 a cross-store audit convicted a spec of drift; the stores were
identical and the audit's own transcription had dropped four lines.*

- **A filename is not provenance (D188).** Hash it.
- **A path in a document is not provenance.** `D:\ClaudeCowork\` was written into three canonical
  places and was wrong in all three. **Look for the folder before reporting it missing.**
- **"Does not mount" is not "unreachable" (S209).** `F:\ClinicBackup` never mounts in the device
  shell and the file-transfer tools read and write it perfectly. Try before declaring.
- **The newer store is not automatically the right store.** Check against what runs.
- **Ask every green check what question it answers.** *S209: `SUMS.md5` green, smoke suite green,
  pin verified, 65 selftests green — and the page's JavaScript had a syntax error that stopped
  every section from loading. **Intact is not valid.***
- **⭐ v15 — A CLOCK TIME IS READ, NEVER ESTIMATED (F-510).** Before writing a time into any canon file,
  read it: `date`, the commit stamp, the file's mtime, or the line a program printed. S262 published a
  close whose times were one and a half to three hours wrong because they were felt, not read.
- **An empty or small result is not good news.** A result that would be pleasant if true gets
  checked harder, not less.
- **A green selftest proves the kit, not the join.** Walk the LIVE shape.
- **Verify a kit gate from INSIDE its own folder** — its rows are rooted there; from anywhere else
  good kits report FAILED (S209 produced exactly one such false RED).
- **⭐ NEW, S258 — A PAGE READ AS TEXT IS NOT THE DATA.** A plain-text read of a live page ran a
  status chip into a vendor's name and produced a finding that reached canon before it was
  retracted. **A page tells you where to look; the store tells you what is true.** Confirm any
  finding taken off a screen against the table, the file or the export behind it.
- **⭐ NEW, S258 — A STORE IS NOT CHECKED UNTIL EVERY ONE OF ITS INCLUSION LISTS IS READ.** A file
  was reported as having no backup on the strength of one list; the same script had a second list,
  and the file was in it. **Reading one of two is how a false gap is minted, and a false gap costs
  what a missed one does.**
- **⭐ NEW, S269 — THE NIGHTLY BUNDLE IS 01:35 EVIDENCE AND NOTHING LATER.** It is a snapshot, and
  a snapshot cannot report what happened after it was taken. *At S269 the assistant read the
  18-Sep bundle, found `freshness_legs.json` unchanged, and told the owner a published kit had
  never been installed — it had been installed that morning, hours after 01:35.* **"The bundle
  does not show it" proves only "not before 01:35".** Ask the live surface first; most kits print
  a read-only `--check` that costs the owner nothing and states the live bytes.
- **⭐ NEW, S269 — A URL IS A LIVE ROUTE OR IT IS NOT PRINTED.** *S269: a kit's closing line sent
  the owner to `/finance/freshness`, which has never existed — the collector writes a file and no
  route serves it.* Before a URL goes into a kit, a message or canon, find it in the app's own
  routes or fetch it. **A dead link in a kit teaches the owner to distrust the kit.**

---

# A · DOCUMENT UPDATES — every step, in order

**A0.1 · Session summary** for the runbook §0. Flag separately: new fault codes, SOP changes,
surveillance-scope changes.

---

## ⭐ A0.2 · READ THE NIGHTLY'S THREE REPORTS — NEW IN v14, AND FIRST

`D:\Downloads\_kbtools\NIGHTLY.bat` runs at **03:10** on manojz as scheduled task
**`KB Manifest Rebuild`**. It runs three things in order and leaves three reports. **Read all three
before any other close step — several later rows are decided by them.**

```
D:\Downloads\_kbtools\REBUILD_REPORT_LATEST.txt
```

```
D:\Downloads\_kbtools\MAINTENANCE_REPORT_LATEST.txt
```

```
D:\Downloads\_kbtools\CANON_SUMS_LATEST.txt
```

| report | written by | what it settles |
|---|---|---|
| `REBUILD_REPORT_LATEST` | `rebuild_manifest.py` (S268) | the Cowork `MANIFEST.md5` — **A13 step 6** |
| `MAINTENANCE_REPORT_LATEST` | `maintenance_nightly.py` (S272) | the VPS code bundle in reach · **the SSD mirror, A14 step 1** · the folder counts |
| `CANON_SUMS_LATEST` | `canon_sums.py` (S275) | `MD5SUMS_ALL.txt` covers `KB_canon_all` — **A8b's safety net** |

**For each one, answer three questions in the close report: does it exist · what is its clock time
· what is its verdict.**

- **Missing** → the nightly did not run. **RED.** Say so, perform that step by hand this close, and
  put the task itself in `OWNER_TODO_LIVE`.
- **Older than 24 h** → the same. A report is evidence of a *run*, not of a *habit*.
- **Verdict WARN or FAIL** → read which step, and treat it as this close's first finding.

**Never quote a figure from these reports without its clock time.** A number with no timestamp is
how a stale reading becomes a current claim.

> **⚠ AND IT DEPENDS ON manojz BEING AWAKE.** The task runs on the owner's personal PC. If that PC
> is off at 03:10 the run is missed — which is why the task is set **"run as soon as possible after a
> scheduled start is missed"**: it then catches up the next time the machine is on. **A catch-up run
> is still a run, but its clock time will not be 03:10 — read the time, not the date.** If a report
> is older than 24 h, the machine has been off for more than a day *and* the catch-up did not fire:
> that is the RED above.


---

**⭐ A0.3 · LIST `KB_canon_all\` IMMEDIATELY BEFORE WRITING ANY CANON FILE — NEW IN v16 (F-534).**
Both projects write into the same folder, and the other one's close may have landed minutes ago
while this session worked. **Append onto the versions that are in the folder now, never onto the
versions read at the open** — at S268 a close appended onto versions superseded three hours
earlier and overwrote two files the other close had just written; they came back only from the
published commit. List the folder, name the newest Register, Archive, Fault Register and Runbook
versions you are appending to, and take the next free D and F numbers from *that* Fault Register's
own end-marker (F-463).

**A1 · KB History Archive (Tier 1) — APPEND ONLY.** Lives in `deploy_kits/KB_canon_all/`, **not in
project knowledge**. Append this session's `§S###` narrative and any full decision text. Never
rewrite earlier history; earlier END markers stay in place as truncation-proofs. **Prove the append
mechanically: hash the previous file, hash the same number of leading bytes of the new one, show
they match, and state the byte count.** Bump the minor version in the END marker only.

**A2 · KB Register (Tier 0) — update current state.** Refresh CURRENT LIVE FILE VERSIONS; add a
one-line index entry for each new decision, authored **from the Archive text, never from memory**
(D172); note state changes; add a changelog line. **Check the four self-referential lines every
time — the H1, the END marker, the how-to-use pointers, and the reserved next-free numbers.** They
are the F-45 family's favourite home; at S207 three of four were stale at once. Corrections are
made **visibly**.

**A3 · Runbook (Tier 0)** — `HANDOFF_RUNBOOK_<date>_Session<N>close_v<N>.md`: §0 what happened ·
§1 mental models · §2 the live backlog · §3 install discipline · §4 the boundary.

**A4 · START_HERE (Tier 0)** — `START_HERE_SESSION_<N+1>.md`. Phase 0 **connects `D:\Downloads`,
`D:\dr-manoj-git` and `F:\ClinicBackup` by name**, verifies `CANONICAL_MANIFEST.md` by md5 across
all tiers while reading only Tier 0, **reads the three nightly reports (A0.2)**, and **opens
`D:\Downloads\ClaudeCowork\00_INDEX.md`**. Carries next-free D/F numbers and the backlog pointer.
**It also states the standing owner rulings in §0 (see the block at the end of this file).**

**A5 · Tier-1 reference docs — only those that actually changed.** For the rest, one line:
*"Tier-1 unchanged this session: [list]"*.

**A6 · Tier-2 frozen products — do NOT touch** without an explicit owner waiver (D34) + version
bump + note.

**A7 · CANONICAL_MANIFEST.md — the linchpin, updated AFTER every document above is final.**
Recompute each md5 and update its row. **A row whose file is absent from project knowledge is not a
failed row — halt on a HASH MISMATCH, never on absence from one store.**

**⭐ A7b · THE MANIFEST'S FOUR SELF-REFERENTIAL SURFACES — NEW IN v14.** The close owns **all four**,
not one. The nightly unattended check has reported for three consecutive nights that three of them
are frozen — the leading narrative blockquote at S239, the STATUS line at S240, and the footer at
S255 — inside the document that *wins on what is current*. **No close step owned them, which is
exactly why they rotted.** They are now this row:

1. the leading narrative blockquote — add this session's paragraph
2. the STATUS line — the current Fault / Register / Archive / Runbook / START_HERE versions
3. the Tier-0 rows — as A7
4. the footer — the next-free numbers and session

**A8 · THE LIVE-PIN LIST — regenerate AFTER A7.**

```
python gen_live_pins.py <KB_Register_vX.md> --manifest CANONICAL_MANIFEST.md \
       --session "S### close" -o live_pins_S###close.txt
```

Confirm the header reads **`register_pin_verified: yes`**. **⭐ v16 (F-513): and state the number of
DECLARED-PENDING rows.** A pin that is a prediction is a promise to read back at the next open;
a promise older than one close is a finding at every close until it is kept. *One stood for
thirty-three sessions and a book called a file unbacked on its strength.* **A close that rebuilds the manifest and
not the pin list is not finished.**

**⭐ A8a · AND GIVE THE PIN LIST ITS MANIFEST ROW — NEW IN v14.** Two consecutive closes generated a
pin list and neither got a row, while two *older* pin lists still claimed CURRENT. **The generated
file gets its row in the same breath it is generated.** F-369 and F-449 in one place.

**A8b · Refresh `deploy_kits/KB_canon_all/` in the same step, and update `MD5SUMS_ALL.txt`
YOURSELF.**

> **⭐ CHANGED IN v14, and this direction matters.** The 03:10 nightly repairs this file — but it
> runs *after* the close, and the publish happens *at* the close. **So the close still owns it.**
> Whenever this close wrote a file into `KB_canon_all`, update `MD5SUMS_ALL.txt` in the same breath,
> before naming the publish. Twice on 15-Sep a document went into canon with no row, and the gate
> then reported *535 of 535 OK* while not checking it at all.
>
> The tool does it without arithmetic:
>
> ```
> D:\Downloads\_kbtools\CHECK_CANON_NOW.bat
> ```
>
> **The nightly is the safety net, not the primary.** State the row count and the verdict.

`verify_live_pins.py` looks in **exactly one folder** for a file hashing to `source_md5` and for the
manifest beside it. A per-close `KB_canon_S###close/` folder does **not** satisfy it.

**A8c · PULL THE VPS DEPLOY CLONE — F-240.**

```
git -C /root/deploy/repo fetch --depth 1 origin main && git -C /root/deploy/repo reset --hard origin/main
```

Every close writes a new Register; the checker proves the pin list against the clone at
`/root/deploy/repo`, which is refreshed only when a kit deploys. **Without this, the checker reports
AMBER `register_not_in_repo` on a box with zero drift after every single close — and an amber that
is normal is an amber nobody reads.** **It rides the next install line's `git pull` (F-464)**, so a
close that ships a VPS kit has already done it; a close that ships none names it for the owner.

**A9 · NOTION SESSION LOG — a hard checkpoint.** Page in **Clinic HQ — Dr. Manoj**
(`38618b9d-8f91-813e-9773-c20f567fd32f`), titled `Session <N> — <date> — <one-line summary>`, with
decisions, findings, and systems-register changes. **Confirm the page URL in the close report.**
**If the API returns 403 / Cloudflare, RETRY ONCE** — at S209 the first call was blocked and the
second succeeded. If the connector is absent, say so explicitly and carry it into START_HERE.

**A10 · `OWNER_TODO_LIVE.md` — refreshed, not appended to.** Deliberately **UN-MANIFESTED**: it
edits continuously and hashing it would make Phase 0 fail by design. Completed ⭐0 items are
**struck through and moved to DONE with the session number**, never deleted. **Nothing gets left
out** — the owner's words when he asked for this.

**⭐ A10b · AND NOTHING GOES IN IT THAT IS NOT HIS — NEW IN v14.** The owner's ruling, 15-Sep-2026:

> *"don't leave it up to my discretion. And make it a part of your routine whenever you deem it to
> be run. Or either run it yourself. You have access to my PC. You have your agent here also."*

**Before an item is written into ⭐0, ask whether the assistant could do it.** A maintenance step
goes into the nightly, or the assistant performs it through the file tools. An action reaches the
owner only when nobody else can take it: **a credential, a GUI, a decision, or a command on the
VPS.** Where something exists only to be *checked*, ship a read-only checker that says on its face
it need not be run — never an installer that implies an owed action.

**⭐ A10c · THE SYSTEM BOARD — NEW IN v15 (D533).** The owner's board is one artifact for both projects —
the portal's **System Board** tile:

```
https://claude.ai/artifact/EtwtRpK4nAbmY98KB4yijk
```

Its database (`board`, `messages`, `_claude_status`) is read at every open; **its page's own words — the
list of what needs him and the "worth knowing" notes — are refreshed at every close**, from the
`OWNER_TODO_LIVE.md` this close just wrote. Read the page's published `index.html` (Artifact `read` with
`path`), change only the `YOURS` and `TELL` lists and the stamp — **never the code** — and republish to the
same URL without passing `capabilities`, so the database carries forward. Each line carries where it
belongs (Pharmacy / Clinic / Personal); keep an existing line's `id` so his ticks and notes stay attached.
Then write `_claude_status` (session, `lastRead`, the close note). **⭐ v16 (D534): the board's
Sanjeevni-plan section is refreshed in the same pass** — what the branching into its own project
now waits on, in one line, so the plan never goes stale on the one surface he reads. **A page that still announces work done
earlier is the F-45 family on the one surface the owner reads.**

**⭐ A11c · KITS ARE BUILT OUTSIDE THE PUBLISH FOLDER — NEW IN v15 (F-512).** `deploy_kits/` is the
publish's pickup area: anything written there is one double-click from GitHub. Build and test in scratch;
copy into `deploy_kits/S###_NAME/` only when final, gated and compiled elsewhere (no `__pycache__` in the
kit). **Once a kit could have been published, it is frozen** — a change is a new kit number, gated on the
old kit's pin. If a published kit folder is disturbed, restore it from git's own objects, not from memory.

**⭐ v16 (F-515): CLAIM THE KIT NUMBER ON THE BOARD BEFORE THE SCRATCH FOLDER IS NAMED.** Two
open chats built two kits under one number because the claim was written after the folder; the
collision was caught only by a rejected board write. The claim costs one line and is the only
thing the other chat can see.

**⭐ v16 (F-300 family): AND IF THE KIT CARRIES A BLANKET-IGNORED FILE TYPE, ADD ITS ALLOW LINE IN
THE SAME BREATH.** `.gitignore` blocks `*.json` wholesale, so a kit with a `.json` in it makes
`PUBLISH_ALL.bat` refuse the entire run — *"at least one file was silently excluded by
.gitignore. Nothing committed or pushed."* — and the owner loses a double-click to a fault that
was knowable when the kit was copied in. Add the exact path, `!deploy_kits/S###_NAME/file.json`,
with a comment naming the kit, and state it in the close report.

**A11 · RE-CAPTURE THE LIVE PC TOOLS — AND VERIFY AGAINST THE LIVE SOURCE.** On any session that
changed a file on **manojz** or the **medical PC**: capture current bytes into
`deploy_kits/S###_LIVE_TOOLS/` with `SUMS.md5`, **then compare every captured file against its LIVE
SOURCE, not against the kit's own sums.** Report both ways. **A kit verified against its own copy
proves nothing about what is running.** Capture also: install order, destinations, which credentials
are needed (**never their values**), scheduled tasks and the account each runs as.

**⭐ A11b · THE VPS's OWN CODE IS NOW READABLE — NEW IN v14, and it is a standing rule.**

```
D:\Downloads\_kbtools\vps_code\code_nightly.tar.gz
```

The 01:35 bundle is copied into that folder by the 03:10 nightly (S272) and since S273 it carries
`/root/assetapp`, `/root/shared`, the allow-listed `/root/deploy` tools and `/root/finance/*.json`
as well. It self-verifies against its own `MANIFEST.md5`.

> **NO PATCHER IS BUILT FROM AN INFERRED ANCHOR WHEN THE REAL FILE CAN BE READ.**
> **NO PIN IS PREDICTED WHEN THE REAL FILE CAN BE HASHED** (F-472).

At S258 this bundle let **109 live pins be held against the box's own bytes in one pass — 109
matched, 0 mismatched.** That check is cheap and repeatable; **run it at any close that touched the
VPS** and state the three counts.

**A12 · THE FIVE STORES, AND THE ONE RULE**

| store | authoritative for | must never hold |
|---|---|---|
| **project knowledge** | canon — everything the manifest names | bulk data, backups, superseded papers |
| **GitHub** | code + `deploy_kits/KB_canon_all/` | patient data, secrets, **phone numbers (F-185)** |
| **`D:\Downloads\ClaudeCowork\`** | everything canon excludes: session kits, working papers, raw data, dated snapshots | **any live, editable copy of a canonical document** |
| **`F:\ClinicBackup\`** (1 TB SSD) | dated frozen mirrors + cold kits | anything that originates there |
| **Google Drive** | the nightly db, the nightly code bundle, the encrypted state bundle | — |

**NO DOCUMENT MAY BE LIVE AND EDITABLE IN TWO STORES** (D202 · F-201). Frozen dated snapshots are
exempt — a dated copy cannot drift into a second live copy.

**⭐ A12b · AND ASK WHAT NO STORE HOLDS — NEW IN v14.** Each store is correct about what it excludes;
the gap lives **between** them. At S258 six files pinned as LIVE had no byte-exact copy in any store
— among them the live item spine, the asset-register application, and the configuration that decides
what the health page watches. **Nothing was positioned to see it until the bundle and the pin list
could be read side by side.** That comparison is now possible at any close (A11b). **Run it whenever
a new live file is pinned, and name anything that would not come back.**

**A13 · THE KB EXTENSION CLOSE — `D:\Downloads\ClaudeCowork\` — MANDATORY, eight steps**

> ⚠ **It is NOT `D:\ClaudeCowork\`.** It sits one level down, inside a folder that is normally
> connected. **This is the whole reason it exists there** — a tidy path you must remember to
> connect is worse than an ugly one that is always there.

1. **`00_CANON_SNAPSHOT_S###\`** — freeze this close's canon: manifest · Archive · Fault Register ·
   Register · pins · `MD5SUMS_ALL`.
2. **`02_SESSION_KITS\S###\`** — every kit this session built.
3. **`03_WORKING_PAPERS\S###\`** — the papers, **and ONE BUILD BRIEF**: the single document the next
   session reads *instead of* ten papers. It goes in **three** places — project knowledge, this
   folder, and loose on the SSD. *Ten papers are a record; one brief is a handover.*
   **⭐ Evidence goes to `03_WORKING_PAPERS\_EVIDENCE\S###\` and is never announced in chat**
   (`PAPER_POLICY_v1.1`). **Report the never-cited percentage at every close. It was 51 % (193 of
   375) at S257. If it does not fall, the policy did not take — say so.**
4. **Copy → verify → only then delete from project knowledge. Never the other way round.**
   *A retirement plan once claimed 22 documents were already safely in a kit. Five were.*
5. **Sweep the bloat** — `__pycache__`, `.pyc`, editor backups, zip temp files — into
   `_to_delete_S###\` **per drive root** (`D:\dr-manoj-git\`, `D:\Downloads\`), each with a
   `WHY_SAFE.txt` naming **every surviving copy and its hash**. Set `PYTHONDONTWRITEBYTECODE=1`
   before running python in these trees and most of it never appears. **Moving is the assistant's;
   deleting is the owner's.**
6. **⭐ CHANGED IN v14 — `MANIFEST.md5` is rebuilt by the 03:10 nightly, not by the close.**
   Read `REBUILD_REPORT_LATEST.txt` (A0.2), **state its clock time, its row count and its verdict**,
   and name what it added, dropped and changed. **This close's own papers land in it at 03:10
   tonight** — say so rather than implying they are already covered.
   **If the report is missing, stale or non-zero, rebuild by hand:**
   ```
   D:\Downloads\_kbtools\REBUILD_MANIFEST.bat
   ```
7. **Update `00_INDEX.md`** with this session's row.
8. **Report project-knowledge usage as MEASURED bytes and percent** of the 2 MB cap — never
   projected from file sizes. *A projection from size was once wrong by more than three times,
   because `knowledge_size` is an indexed measure.*

**A14 · THE SSD — `F:\ClinicBackup\`, one folder per project**

```
F:\ClinicBackup\DrManojClinic_Automation\
   01_KB_MIRRORS\    a dated zip of the Cowork folder      -- taken NIGHTLY since S272
   02_COLD_KITS\     dated cold kits                       -- see E
   03_BUILD_BRIEFS\  the loose brief                       -- EVERY close
   99_SUPERSEDED\    older copies awaiting the owner's delete
```

1. **⭐ CHANGED IN v14 — the mirror is taken nightly, not at the close.** `maintenance_nightly.py`
   writes `KB_mirror_ClaudeCowork_nightly_<date>.zip`, reopens it and tests every CRC, and moves
   all but the newest 14 into `99_SUPERSEDED\`. **The close VERIFIES it: list the folder back, name
   the newest mirror, its date, its size and its file count.** *A mirror nobody refreshes is a copy
   that lies — and a mirror nobody looks at is the same thing.*
   **If the newest mirror is not from today, the nightly did not run: say so and take one by hand.**
2. **A file loose at the root has no owner.** In six months nobody knows which project it belonged
   to. **A folder name is the cheapest provenance there is.**
3. **Retention:** the nightly keeps the **14** most recent KB mirrors; the close keeps the **5**
   most recent cold kits, older to `99_SUPERSEDED\`. Keep **every** build brief — they are tiny and
   they are the decision record.
4. **The disk cannot be deleted from by a session.** So **refresh `99_HOUSEKEEPING_TODO.md` at the
   root every close**, naming each file to delete, its size, and **where its surviving copy is,
   proven**. *A vague instruction to tidy up is one nobody acts on.*
5. **Never propose deleting anything whose surviving copy has not been PROVED.** At S209 two
   superseded mirrors were only proposed for deletion after opening all three zips and comparing
   every file inside them by CRC.

**A15 · REDUCE PROJECT KNOWLEDGE BY ONE TRANCHE — every close, in order**

1. the **22 S206 papers** — six superseded outright, and those are the most dangerous documents in
   the KB: a future session can read them as current and get wrong numbers
2. superseded runbooks (v113, v134, v138, v139) and the `Fault_Register_append_*` artefacts
3. **S179 – S184**, oldest first
4. **S194 – S202**, after confirming every D-number is indexed in the Register
5. **S205 — LAST**, and only after the §S205 gap is ruled on: those seven documents are the only
   surviving record of that session

**⛔ NEVER MOVE**, whatever the manifest says: the evergreen `START_HERE_PROMPT`, the current
`live_pins_*`, `OWNER_TODO_LIVE.md`, `UNATTENDED_QUEUE.md`, open work orders, and **any INCIDENT
document not confirmed closed**. **Report the measured `knowledge_size` before and after.**
Or state why no tranche moved.

**⛔ AND NEVER MOVE A DOCUMENT THAT IS ITS OWN ONLY COPY.** At S257 six were named and kept for
exactly that reason — *"they are not in `KB_canon_all`, and an unproven copy is not a copy."*
**Prove the copy first, by hash, in the store that will keep it.**

**A16 · THE PUBLISH — the owner's double-click.** *"publish all, i will do, your method is very
slow."* The assistant prepares, clears anything that would block the run (a stale
`.git\index.lock` — **never run `git` against the mounted repo, F-233**), and names **ONE file with
its full path**:

```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```

**⭐ v15 (F-511): and never run `git` in `device_bash` either.** Before naming the publish, confirm
`.git` holds no `*.lock` (a `find`, not a git command); a lock the assistant's shell left is MOVED out of
the repository into `D:\dr-manoj-git\_to_delete_S###\`, never left for the owner's double-click.

State what is pending in that publish. The F-185 phone gate is inside the bat; if it refuses, the
refusal text is the finding.

**⭐ v16: two refusals, not one.** The bat also refuses when a staged file is
**silently excluded by `.gitignore`** and commits nothing at all; the fix is the exact-path allow
line (A11c), and it belongs in the kit's own breath, not in the owner's next message. **And every
URL this close prints — in a kit, in a message, in canon — is checked against the app's routes
first (A0).**

**⭐ A16b · AND VERIFY THE PUBLISH LANDED — NEW IN v14.** Do not close on the word "published".
Prove it **without git in the PC shell (F-511)** — read `.git/logs/HEAD` and `refs/remotes/origin/main`
(the push updates both) or clone in the cloud workspace: **the commit hash and its clock time**, every canon file this
close wrote present at the hash it was written at, and **`md5sum -c MD5SUMS_ALL.txt` run from inside
`KB_canon_all`, with the count stated.** At S258 the first publish landed the document and left the
gate not covering it; only reading it back found that.

---

# ⭐ A17 · THE CLOSE-REPORT CHECKLIST — MANDATORY

**Every row answered `DONE` / `BLOCKED (reason)` / `OWED`. A row may not be omitted, and silence is
never DONE.** A step that could not run says why, and moves to `OWNER_TODO_LIVE` in the same breath.
**Name which folders were connected this session** — several rows depend on it.

| # | step | done means |
|---|---|---|
| 0 | **The three nightly reports (A0.2)** | **each one: exists · clock time · verdict.** Missing or stale is a RED, not a blank |
| 1 | Archive (A1) | appended, prefix proven, byte count stated |
| 2 | Fault Register | findings minted or explicitly OWED |
| 3 | KB Register (A2) | current-state rows + the four self-referential lines |
| 4 | Manifest (A7) + **its four surfaces (A7b)** | updated last; narrative, STATUS, rows and footer all written |
| 5 | Runbook + START_HERE (A3/A4) | next entry point written |
| 6 | `OWNER_TODO_LIVE` (A10) + **nothing in it that is not his (A10b)** | refreshed |
| 7 | Live pins (A8) + **its manifest row (A8a)** + **canon sums (A8b)** + **clone pulled (A8c)** | `register_pin_verified: yes`; sums count and verdict stated |
| 8 | **NOTION** (A9) | page URL quoted |
| 9 | **KB EXTENSION** (A13) | all eight steps answered, **never-cited % stated** |
| 10 | **SSD** (A14) | **nightly mirror verified by listing back**, newest named with date/size/count |
| 11 | Cleanup (A13.5) | `_to_delete_S###\` per drive root with `WHY_SAFE.txt` |
| 12 | Reduction tranche (A15) | moved, with measured before/after — or why not |
| 13 | Publish (A16) + **verified landed (A16b)** | file named, contents stated, commit hash and gate count quoted |
| 14 | **The four numbers** | drift · dead · folders · stale — measured, never projected |
| 15 | **What no store holds (A12b)** | run when a new live file was pinned, or state why not |
| 16 | **⭐ The System Board (A10c)** | page words refreshed and republished to the same URL; `_claude_status` written |
| 17 | **⭐ v16 — PENDING pins (A8, F-513)** | the pin check's three counts **plus the DECLARED-PENDING count** |
| 18 | **⭐ v16 — `.gitignore` allow lines (A11c)** | every blanket-ignored file a kit carries has its exact-path `!` line, quoted |
| 19 | **⭐ v16 — the canon folder was listed first (A0.3, F-534)** | the four versions appended to, named as they were found in the folder |

---

# B · LIVE SYSTEM ACTIONS

- **Notion** (the session log is A9): also update any Tech & Systems Register status that changed,
  move Active Projects cards, add new D-series decisions.
- **Drive:** upload new/updated Tier-0/Tier-1 files, version-named.
- **Drive incident report:** only if an incident actually occurred.
- **Gmail (EOS only):** if `Diagnostics.gs` is not live and a manual health check was done, draft a
  brief note to `drmkaortho@gmail.com`.
- **ClickUp is parked (D17)** — not part of this routine.

# C · GITHUB COMMIT (EOS only)

```
Session <N>: <one-line summary>

- <file or change 1>
- Docs: Register/Archive/manifest updated as needed
- Diagnostics: <fault code or check changes>
```

**Run `deploy_kits\NO_PHONE_NUMBERS.py` before proposing the commit (F-185).**

# D · PROJECT KNOWLEDGE SWAPS

- **Tier 0 — almost always:** KB Register · Runbook · START_HERE · CANONICAL_MANIFEST, plus
  `OWNER_TODO_LIVE.md` per A10, updated in place and never version-swapped.
- **Tier 1** — only if A5 flagged it changed. **Tier 2** — never, unless a waiver was exercised.

# E · COLD KIT

**Take one when EITHER is true: three sessions since the last, OR the Register or Archive just
bumped a version** — whichever comes first; on an active project the bump usually does.

**Contains:** the canon set · this session's kits · the pin file · `SUMS.md5` over all of it · and
`00_READ_FIRST.md` saying how to restart from the kit alone. **No patient data, no phone numbers, no
tokens** — and put `NO_PHONE_NUMBERS.py` *inside* the kit so a restored copy still enforces it.

**Goes to** `F:\ClinicBackup\DrManojClinic_Automation\02_COLD_KITS\` **and** `D:\Downloads\`.
**Record every time: what was taken, its md5/size, where it went, and when the next is due.**

# F · THE SWITCHES — know what can be stopped, before you change it

Every scheduled job on all three machines can now be stopped by a file. **A kit that changes a
guarded job may switch it off first and on afterwards** — that is what they are for.

| machine | folder | all-off marker |
|---|---|---|
| **VPS** — spine, attribution, export watch, salts refresh | `/root/finance/_off/` | `ALL_OFF` |
| **VPS** — Marg collector and shadow | `/root/marg_ingest/` | `OFF` (its own, older) |
| **manojz** | `D:\Downloads\margsync\_off\` | `ALL_OFF.txt` |
| **medical PC** | `D:\SendToClinic\_off\` | `ALL_OFF.txt` — **does not stop capture, by design** |

One line shows and changes the VPS side:

```
bash /root/finance/sanjeevni_switch.sh status
```

**⚠ `ALL_OFF` on the medical PC does not stop capture.** Marg reuses one file name for every export,
so an export not captured in that instant is gone for ever. Stopping capture takes its own marker,
put there on purpose.

# G · MAINTENANCE PROJECT CHECK — dormant until that project exists

---

# ⭐ THE STANDING OWNER RULINGS — restate these in every START_HERE

1. **Publishing is HIS double-click.** Name one file, full path.
2. **Full paths ALWAYS — including URLs**, each in its own copy block. Never a bare `/finance/...`
   in prose.
3. **ONE line per command.** A multi-line paste has twice been cut in transit or had its next line
   swallowed by a `cp -i` prompt. Use `\cp` to bypass the alias.
4. **Token-lean working — never at the cost of verification.**
5. **Plain language. One step at a time. Full-file replacements. ALL-CAPS = urgent.**
6. **Mask patient numbers (last 4) and never print secrets or tokens.**
7. **Nothing live is rebuilt without his OK; the manual path stays as fallback.**
8. **Sub-agents read screens** — screenshots never enter the main conversation.
9. **Do not hand him diagnostics to run.** Do the background work; ask for the one action nobody
   else can do — a GUI step, a credential, a decision — in one line.
10. **When a screen is wrong, read the screen's code FIRST.** The server is the last suspect.
11. **⭐ Do not hand him a step that is not his (A10b).** If the assistant can do it, the assistant
    does it — or the nightly does.
12. **His board carries only what needs him and what he should know (D526)** — and every close keeps
    its words current (D533).
13. **His own items are deferred** (17-Sep: *"until and unless urgently required"*). Name only what has
    become urgent, and say why.

---
*v16 · 18-Sep-2026 · S269 · SELF-CONTAINED. Supersedes v15 whole (v15 · 17-Sep-2026 · S263 superseded v14 whole, which superseded v13 whole).
If a step is not written in this file, it is not part of the close. The four steps the nightly now
owns are VERIFIED here, never assumed — a missing report is a RED. And no claim about what is
live rests on the nightly bundle alone: a snapshot cannot report what happened after it was
taken.*
