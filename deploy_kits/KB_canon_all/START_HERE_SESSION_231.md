# START HERE — SESSION 231

Hi Claude. Continuing my clinic-automation project — **Session 231**.
I'm Dr. Manoj Agarwal, orthopaedic surgeon, Advanced Orthopaedic Surgery Centre, Bareilly.
Solo practice, older Hindi-first semi-urban patients.

---

## §0 · THE STANDING OWNER RULINGS — restated every session

1. **Publishing is HIS double-click.** Name one file, full path.
2. **Full paths ALWAYS — including URLs**, each in its own copy block. Never a bare `/finance/...`.
3. **ONE line per command.** Use `\cp` to bypass the alias.
4. **Token-lean working — never at the cost of verification.**
5. **Plain language. One step at a time. Full-file replacements. ALL-CAPS = urgent.**
6. **Mask patient numbers (last 4); never print secrets or tokens.** F-185: no number at all in the repo.
7. **Nothing live is rebuilt without his OK; the manual path stays as fallback.**
8. **Sub-agents read screens** — screenshots never enter the main conversation.
9. **Do not hand him diagnostics to run.** Ask for the one action nobody else can do, in one line.
10. **When a screen is wrong, read the screen's code FIRST.** The server is the last suspect.
11. **English to him, always.** Hindi is a staff-side requirement only.
12. **Do not put technical or architectural choices to him.** Make the call, state it in one line, proceed.
13. **Chat output SHORT.** Long write-ups belong in project documents.

**Earned at S229 and it outranks a script:** *when the owner tells you something about his own shop,
check it against the data before restating what a tool says.*

**⛔ TWO STANDING HOLDS — D414, restate until lifted.**
**(a) The ICICI bank ingest is LIVE and load-bearing.** What he retired was the **email digest**; the
bank leg lives in the same Apps Script project. Do not disarm any trigger.
**(b) The callback tracker is not to be touched at all.**
All other Apps Script work is **parked** until Phases 1 and 2 complete. **Bitwarden is parked** too.

---

## PHASE 0 — CONNECTIONS, then verification, then work

**1 · CHECK THE CONNECTIONS AND PROMPT HIM. Before anything else.**

| needed | what breaks without it |
|---|---|
| **`D:\Downloads`** | no Marg archive, no `_config`, no ClaudeCowork — the KB extension |
| **`D:\dr-manoj-git`** | no repository, no kits, no publish |
| **`F:\ClinicBackup`** | the close cannot mirror or take a cold kit |
| **`H:\My Drive\FinanceDB_Backups`** | the VPS's nightly `finance.db`, so nothing is copied by hand |

⚠ **`F:` and `H:` never mount in the device shell — that does NOT mean unreachable.** The
file-transfer tools read and write both perfectly. ⚠ **The assistant's browser is still in the F-242
login loop**; the owner can supply a live page read by saving the page and uploading it, and that
route works.

**2 ·** Open **`CANONICAL_MANIFEST.md`**. The one live copy is
`deploy_kits/KB_canon_all/CANONICAL_MANIFEST.md`; the project-knowledge copy is a replica.

**3 · Verify every row by md5, from INSIDE `KB_canon_all`.** Halt on a hash mismatch only; a row
absent from one store is not a failed row.

**4 · Read only Tier 0:** manifest · this prompt · KB Register **v5.80** · Runbook **v162** ·
`OWNER_TODO_LIVE.md` · any open incident.

**5 ·** Open `D:\Downloads\ClaudeCowork\00_INDEX.md` and read **`S231_BUILD_BRIEF.md`** — one brief
instead of ten papers.

---

## §1 · THE FIRST THING TO DO AT THIS OPEN — read four pins back from the box

The S230 close recorded **four VPS pins as PREDICTIONS from published kit bytes**, DECLARED-PENDING.
Ask him for one line and compare:

```
md5sum /root/state_backup/clinic_state_backup.py /root/finance/verify_restore.py /root/finance/freshness.py /root/finance/freshness_legs.json
```

Expected: `425e77f5…` · `f67ee579…` · `6476d1d2…` · `ad223bc6…`

**And the real proof of the session's main build:** the freshness page ran unattended at 08:05.

```
tail -3 /root/finance/freshness.summary.log
```

Every leg inside its window and a fresh `legs=26` line dated today means the layer is alive. **A
missing 08:05 line is the finding.**

---

## §2 · THE BACKLOG — Runbook v162 §2 is canonical

**Next: 1.6 credential consolidation** (the Marg token in five places; the spare service-account key
copies; the master-credentials spreadsheet in `D:\Clinic backups`; the MyOperator literals; and
**F-358, the ntfy topic hard-coded in two copies in the repository**). Then **1.7** the self-advancing
renewals register plus the eight missing technical vendors, Tailscale first. Then **1.9**, the
medical PC capture chain that runs only inside his logon session.

---

## §3 · WHAT S230 LEFT RUNNING THAT DID NOT RUN BEFORE

- **01:50 nightly** — the off-box state backup: 55 files, AES-256, off the box, monthly pinned forever.
- **08:05 daily** — the freshness layer: 26 legs, one page, one shout, at most once a day per leg.
- **Twice yearly** — the restore drill, which proves a backup can actually be opened.

**Do not treat any of these as decoration.** Before S230 this estate had no way to notice that
something had stopped. If one of them is silent, that silence is the highest-priority item on the
page.

---
*START_HERE_SESSION_231 · generated at the S230 close, 07-Sep-2026. Next free: **D419 · F-363**.*
