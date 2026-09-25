# drmanoj-clinic-automation — CLAUDE.md (rulebook for Claude Code)

Read this first in any session touching this repository. Written 25-Sep-2026 by the Sanjeevni chat (S283, D617).
Clinic and pharmacy (Sanjeevni) automation of Dr. Manoj Agarwal. His personal health apps live in
`D:\dr-manoj-git\drmanoj-health-systems` — **do not mix the two repositories.**

## Who you work for, and how
- The owner is a surgeon, **not a technical person**. Plain English, short. Never put a technical choice to him —
  decide, say what you decided in one line, carry on. Stop only for what nobody else can do (a password, a decision
  about what a screen shows). Times in **IST** always.
- The work comes as a **brief** in `claude_code_briefs\` written by the Sanjeevni or clinic chat. The brief is the
  whole scope. Anything outside it: do not touch; name it in the report instead.
- The owner has already approved the WHAT of every brief. Do not ask him again. Build, test, install, verify,
  publish, report — in one run.

## The server
- Hostinger VPS **srv1746119** — the SAME server as the health apps; reach it the way you already do for
  `drmanoj-health-systems`. Public site: `https://followup.dr-manoj.in`.
- **Live money records are on this server.** `/root/finance/finance.db` holds every pharmacy and clinic rupee.
  One Flask process `clinic-finance` (port 8106, `/finance/healthz` is the only public health route), the portal
  `clinic-portal` (`/root/portal/`). VPS python for jobs: `/root/wa/venv/bin/python3`; the service uses `/usr/bin/python3`
  — a file must compile on both.
- The repository's clone on the server is `/root/deploy/repo`.

## THE SAFETY RULES — every one, every time (each was paid for by a real fault)
1. **Pin before touching.** For every live file you change, read its md5 first and compare with the FROM pin in the
   brief. Different = someone changed it since the brief: STOP that file, report it. Never patch blind.
2. **Build from the live bytes.** Patch with a script that makes anchored edits (each anchor must occur exactly once,
   else stop) — or a full-file replacement built from the live file. Never re-type a file.
3. **Test on a copy of the live database, never the live one.** Copy with the sqlite backup API
   (`sqlite3.connect(src).backup(dst)`), never `cp` a live database. The walk (test) uses its OWN rows, found by key,
   never by counting (a real row in the live data broke two walks that counted).
4. **Every test must be able to fail.** Include a negative control: run the same test against the OLD file and show
   it goes red.
5. **Health probes:** `/finance/healthz` must answer 200. Any other page answers 302 to a plain curl (login gate) —
   that is EXPECTED, never a failure. (Three installs rolled themselves back by testing a login-gated route.)
6. **Back up before placing:** `finance.db.bak_S###_<stamp>` with the backup API; `<file>.bak_S###_<from8>` beside
   every file you replace.
7. **Place, then read the md5 back** and compare with what you built. Restart only the service the brief names.
8. **If anything is red after placing: restore every file byte-identically, restart, confirm healthz 200, and
   report.** Never leave the box half-changed. The database backup stays.
9. **Never touch a file the brief does not name.** Files that belong to the clinic side (`finance_app.py`,
   `portal.py`, `tile_grants.json`, backups, `/root/state_backup/`, crontab) are touched only where the brief says so.
10. **No patient data, phone numbers, account numbers, tokens or passwords** in the repository, in a test fixture,
    a commit message or the report. Mask a patient/phone number to its last 4. Run
    `python -B deploy_kits\NO_PHONE_NUMBERS.py --files-from <list> .` over every file you add before publishing.
11. **No `__pycache__` / `.pyc` inside the repository** — run python with `-B`, never import from inside `deploy_kits\`
    (copy the module out first). A published kit folder is frozen: never edit it; a fix is a new kit number.
12. **Staff pages are in Hindi (Roman script), the owner's pages in English.**
13. A clock time you report is READ (a program's output, a file time), never estimated.

## How a build is packaged (keep the estate's shape)
- Each build is a **kit**: `deploy_kits\S###_NAME\` with the new files, `make_*.py` (the anchored patcher),
  `walk_*.py` (the test), `install_S###_NAME.sh` (gates → pin check → compile both pythons → walk on a scratch copy →
  backup → place → md5 read-back → restart named service → healthz → restore on red), `README.md` (what, why, pins
  FROM → TO, what it touches), `KIT_ID.txt` (first line `kit id S###_NAME`), `SUMS.md5`.
  Look at `deploy_kits\S399_DAY_TRUTH_5\` as the model.
- The kit number, and any D/F number, is **given in the brief** — never invent one.
- Run the installer ON THE SERVER from `/root/deploy/repo` after the owner's repository is updated, or copy the kit
  folder to the server and run it there — either way the kit in the repository must be byte-identical to what ran.
- **Publish:** when the kit is final, run `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` yourself (it
  gates, commits and pushes). If it refuses, fix the cause (never work around the gate) and run it again.

## The report (the owner and the chat both read it)
Write `claude_code_briefs\REPORT_S###.md`:
- 3–6 plain-English lines for the owner at the top: what changed, on which screen, for whom, and that it works.
- Then for the chat: every live file FROM → TO md5 read back on the box; the walk's output; the negative control;
  backups made; services restarted; anything you did NOT do and why; anything outside the brief you noticed.
Then tell the owner in the Claude Code window, in two lines, that it is done and working (or what stopped it).

## If the owner says "undo"
Put back the `.bak_S###_<from8>` files of that kit, restart the named service, healthz 200, read the md5s back,
report. The database backup is used only if the brief's data change must be reversed — say so before using it.
