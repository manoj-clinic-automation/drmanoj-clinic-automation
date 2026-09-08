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

**Next free: D428 · F-372 · Session 233.**

**Genuinely blocked:** the WABA rotation, on **Ms. Khushi Jain's** answer — *do the old and new
tokens overlap?* **Nothing else in the plan waits on anything.**

**Held by the owner, both his rulings of 08-Sep:** the **PWA install** waits until the restructure
exercise is done · **Sanjeevni/Marg stays in this project** — develop it, then decide the split.

---

## §3 · WHAT S233 DOES — in the owner's order

**1 · Back up the Apps Script projects and the live Sheets.** The last way this estate can lose data
quietly: **eleven** projects across two accounts (not nine — "CC saver" is the tenth, on the personal
account) and seven Sheets, with no backup anywhere. **D426 put Drive reads and writes in scope**, so
it can run unattended. `claude/S232_APPS_SCRIPT_TRIGGERS_READ.md` says which are actually armed.

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
*START_HERE_SESSION_233 · written at the S232 close, 08-Sep-2026.*
