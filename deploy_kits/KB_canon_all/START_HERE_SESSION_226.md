# START HERE — SESSION 226

*Generated at the S225 close, 06-Sep-2026 04:00 IST. The evergreen custom-instructions prompt is `START_HERE_PROMPT` v8; this is the session entry point. Read this, then `CANONICAL_MANIFEST.md`, then `KB_Register_v5_74_S225.md`, `HANDOFF_RUNBOOK_2026-09-06_Session225close_v157.md`, `OWNER_TODO_LIVE.md` — and `S225_BUILD_BRIEF` instead of the S225 papers.*

---

## §0 · THE STANDING OWNER RULINGS — read first, every session

1. **Publishing is HIS double-click.** Name one file, full path. Never drive the desktop for it.
2. **FULL PATHS ALWAYS — including URLs**, each in its own copy block. Never a bare `/finance/...`.
3. **ONE line per command.** Multi-line pastes have twice been cut in transit. Use `\cp`.
4. **Token-lean working — never at the cost of verification.**
5. **Plain language. One step at a time. Full-file replacements. ALL-CAPS = urgent.**
6. **Mask patient numbers (last 4) and never print secrets or tokens.**
7. **Nothing live is rebuilt without his OK; the manual path stays as fallback.**
8. **Sub-agents read screens** — screenshots never enter the main conversation.
9. **Do not hand him diagnostics, investigations or A/B tests.** Do the background work; ask for the one action nobody else can do — a GUI step, a credential, a decision — in one line.
10. **When a screen is wrong, read the screen's own code FIRST.** The server is the last suspect.
11. **Do not put technical or architectural choices to him.** Make the call, state it in one line, proceed. He rules on what he can SEE: a screen, a wording, a workflow, a priority.
12. **He wants to be part of the PWA build** — the product and the flow, never the implementation.
13. **Keep chat SHORT.** *"less for me to read, its your turf."* Long write-ups go in project docs.
14. **English to him, always.** Hindi is staff-side only.
15. **Supplier-wise is FINAL for month-end; Marg's purchase returns are normal** (D368).
16. **Staff pages may be all-English** (D369).
17. ***"And such lines also"*** — no per-type counts on a card he reads. Three plain lines, or nothing.
18. **A registration or install handed to him must show its result in a window that stays open** (S225: a pasted PowerShell line ran and vanished unread; the `.bat`-that-pauses is the form).
19. **Tread safely when he says so** — *"stop and confirm from me if needed"* (S225, 20:00): before a step that touches money data or a security rule, one line of plan, then wait.
20. **The daily Marg routine is his D376:** the sale report every morning for the last two days; closing stock every morning after purchases; stock-check mornings run purchases → the two purchase reports → closing stock → count.

---

## PHASE 0 — CONNECTIONS, then verification, then work

1. **Check the connections and prompt him by name:** `D:\Downloads` · `D:\dr-manoj-git` · `F:\ClinicBackup` (never mounts in the device shell; the file-transfer tools reach it) · the assistant's browser (F-242 login loop — needs his sign-in).
2. Open `CANONICAL_MANIFEST.md`; **verify every row by md5** (`md5sum -c MD5SUMS_ALL.txt --quiet` from inside `deploy_kits/KB_canon_all/`); halt on a hash mismatch only.
3. Read only Tier 0: manifest · this file · Register v5.74 · Runbook v157 · `OWNER_TODO_LIVE.md`.
4. Open `D:\Downloads\ClaudeCowork\00_INDEX.md` and `03_WORKING_PAPERS\S225\S225_BUILD_BRIEF.md`.
5. **Never run `git` against the mounted repo (F-233)** — `ls`/`find` to look; a stale `index.lock` is renamed into `_stale_git_locks_S###\`, never deleted by the bridge.

---

## ⭐ FIRST ACTIONS AT S226

1. **Read the drift page's Sunday** — did Amir's purchase exports (06-Sep morning) land, did the pull cycle send the purchase books and recompute our figure within ten minutes, did the 13 below-zero items resolve? The logs: `D:\Downloads\margsync\_analysis\expected_on_capture_log.txt` and `push_stock_log.txt`. **This is the proof that gates ⭐1 item 2 (server-side computation).**
2. **The readiness header + logged check result** on the drift and count pages (⭐1 item 1) — his spec, verbatim in `S225_STOCK_CHECK_READINESS` §7.
3. **A8c — pull the VPS deploy clone** if the close's publish landed after the last kit deploy: `git -C /root/deploy/repo fetch --depth 1 origin main && git -C /root/deploy/repo reset --hard origin/main` (his one line).

---

## THE BACKLOG POINTER

**`HANDOFF_RUNBOOK_2026-09-06_Session225close_v157.md` §2** — ⭐0 his actions (wall-card reprint · August advances on the ledger · the S182 tiles word · FINALISE · the delete lists) · ⭐1 the readiness header and logged result → the server-side computation → the S208 kit revision (F-319 · F-322 · F-323) → Marg pending → the 17 phone numbers → the NEFT files → the loans PWA view, procedures (D373), the S223 dawn specs, the tracker parser fix.

---

## NEXT FREE NUMBERS

**D377 · F-324 · Session 226.**

---

## THE FIVE STORES, AND THE ONE RULE

project knowledge = canon · GitHub = code + `deploy_kits/KB_canon_all/` (**no numbers, F-185**) · `D:\Downloads\ClaudeCowork\` = everything canon excludes · `F:\ClinicBackup\` = frozen mirrors and cold kits, one folder per project · Google Drive = the only phone-readable route, still not set up.

**NO DOCUMENT MAY BE LIVE AND EDITABLE IN TWO STORES** (D202 · F-201). Dated frozen snapshots are exempt. **No canonical document is a delta.** **The manifest WINS on what is current.**

---
*START_HERE_SESSION_226 · generated at the S225 close, 06-Sep-2026.*
