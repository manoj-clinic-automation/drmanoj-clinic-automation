# START HERE — SESSION 241

*Written at the S240 close, 12-Sep-2026 IST. Read this, then `HANDOFF_RUNBOOK_2026-09-12_Session240close_v171.md`.*

---

## §0 · THE STANDING OWNER RULINGS — they govern every session

1. **Publishing is HIS double-click.** Prepare, clear blockers, name ONE file with its full path:
   `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
2. **Full paths ALWAYS — including URLs**, each in its own copy block. Never a bare `/finance/...`.
3. **ONE line per command.** Use `\cp` to bypass the alias.
4. **Token-lean working — never at the cost of verification.**
5. **Plain language. One step at a time. Full-file replacements. ALL-CAPS = urgent.**
6. **Mask patient numbers (last 4) and never print secrets or tokens.** F-185: no number at all in the
   repository.
7. **Nothing live is rebuilt without his OK; the manual path stays as fallback.**
8. **Sub-agents read screens** — screenshots never enter the main conversation.
9. **Do not hand him diagnostics, investigations or A/B tests.** Ask for the one action nobody else can
   do — a GUI step, a credential, a decision — in one line.
10. **When a screen is wrong, read the screen's own code FIRST.** The server is the last suspect.
11. **Do not put technical or architectural choices to him.** Make the call and state it in one line.
12. **English with him; Hinglish on staff pages.** IST always.
13. **Keep chat SHORT** (*"less for me to read, its your turf"*). Long write-ups go into project documents.

---

## §1 · PHASE 0 — CONNECTIONS FIRST, EVERY TIME

| needed | what breaks without it |
|---|---|
| **`D:\Downloads`** | no Marg archive, no `_config`, no `ClaudeCowork` — the KB extension |
| **`D:\dr-manoj-git`** | no repository, no kits, no publish |
| **`F:\ClinicBackup`** | the close cannot mirror or take a cold kit |
| the assistant's browser | no live-page reads |

⚠ **The device shell has mounted nothing since the Windows update of 8-Sep** — three sessions running.
The method that works every time: **stage → edit in the container → commit → re-stage → md5**.
⚠ **`F:` never mounts in the device shell and that does NOT mean unreachable** — the file tools read and
write it perfectly.
⚠ **Verify a kit gate from INSIDE its own folder**; from anywhere else good kits report FAILED.

Then open `CANONICAL_MANIFEST.md`, verify rows by md5 (halt on a MISMATCH, never on absence from one
store), read Tier 0 only, and open `D:\Downloads\ClaudeCowork\00_INDEX.md` and `S240_BUILD_BRIEF`.

**Canon at this close:** Archive **v1.87** · Register **v5.90** · Fault Register **v2.72** (F-0 … F-438) ·
Runbook **v171** · this file · `S240_BUILD_BRIEF` · manifest.
**Next free: D478 · F-439 · Session 241.**

---

## §2 · WHAT TO START ON

### §2a · FIRST — REPRINT AUGUST AND LOCK IT

The money is settled. Since the last print: the footnote is right (÷30.5), Amir shows no leave working,
Darpan is off Sheets 3 and 4 and has two pages of his own at the end, and **every NET PAYABLE now ends in
a zero** (D477). So the sheet he has in his hand is out of date — reprint before locking.

```
https://attendance.dr-manoj.in/register/salary/flow/preview?ym=2026-08
```

```
https://attendance.dr-manoj.in/register/salary/flow?ym=2026-08
```

**Do not lock it for him.** The lock is his alone, and it will be the first salary month ever locked.

### §2b · D467 PHASE 2 REMAINDER — the medical PC

Three things are left before the move is finished:

1. **Start at power-on, not at logon.** One visit, one double-click, plus a single-instance lock inside
   `medical_agent.py` so the two starts can never both run.
2. **The Drive copy of each capture**, and sharing `FromMedical` with the service account — the second
   leg, so a dead HTTPS path is not a dead pipeline.
3. **The "no export today" alarm (2c)** — the server notices silence by itself.

Then **phase 3** (retire manojz's data jobs) and **phase 4** (manojz = development only).

### §2c · AMIR AND DARPAN

Amir's **seven screens** are drawn and waiting on his yes. When it comes, build the PWA exactly as drawn:
a 1 → 7 banner, an on-screen confirmation after each step, a bill list with a per-bill drop-down of what
to enter (enterable and skippable), and a visible **DAY CLOSED** screen. Then **the claim queue** on
Darpan's PWA (D471). D472's CROCAL reading still needs his confirmation.

### §2d · CARRIED DEBT

- The repository copy of `medical_agent.py` is the stale **S203.3**; live is **S205.1 70d5c4e3** — replace.
- The unmasked `marg_report.py` on manojz and the medical PC → replace with **eeab5605** (F-185).
- ~300 stray `marg_watch.py.before_*` files on the medical PC — **deleting is his**; a list is prepared.
- manojz's Task Scheduler to be read back when the device shell works.
- **DECA INSTABOLIN 50 +5** still unexplained, and recorded as unexplained (F-434).
- **F-436 parked at his word:** Marg's purchase serial is in no export; capturing it means Amir types it.
- Parked at his word: the weighted / allowed columns on the salary sheet.

---

## §3 · THE FIVE STORES, AND THE ONE RULE

project knowledge = canon · GitHub = code + `deploy_kits/KB_canon_all/` (no numbers, F-185) ·
`D:\Downloads\ClaudeCowork\` = everything canon excludes, plus dated snapshots and session kits ·
`F:\ClinicBackup\` = frozen mirrors + cold kits, one folder per project · Google Drive = the only
phone-readable route, and now also the KIT_MANIFEST delivery channel to the medical PC.

**NO DOCUMENT MAY BE LIVE AND EDITABLE IN TWO STORES** (D202 · F-201). **The manifest wins on what is
current.**

*START_HERE_SESSION_241 · written at the S240 close, 12-Sep-2026.*
