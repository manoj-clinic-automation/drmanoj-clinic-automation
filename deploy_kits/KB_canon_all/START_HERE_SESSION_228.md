# START HERE — SESSION 228

*Generated at the S227 close, 06-Sep-2026 22:00 IST. The evergreen custom-instructions prompt is `START_HERE_PROMPT` v8; this is the session entry point. Read this, then `CANONICAL_MANIFEST.md`, then `KB_Register_v5_76_S227.md`, `HANDOFF_RUNBOOK_2026-09-06_Session227close_v159.md`, `OWNER_TODO_LIVE.md` — and **`S228_BUILD_BRIEF`** (the owner's rulings for this session) with `S227_BUILD_BRIEF` (what is live) instead of the twelve S227 papers.*

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
11. **Do not put technical or architectural choices to him.** Make the call, state it in one line, proceed. He rules on what he can SEE.
12. **He wants to be part of the PWA build** — the product and the flow, never the implementation.
13. **Keep chat SHORT.** *"less for me to read, its your turf."* Long write-ups go in project docs.
14. **English to him, always.** Hindi is staff-side only.
15. **Supplier-wise is FINAL for month-end; Marg's purchase returns are normal** (D368).
16. **Staff pages may be all-English** (D369).
17. ***"And such lines also"*** — no per-type counts on a card he reads. Three plain lines, or nothing.
18. **A registration or install handed to him must show its result in a window that stays open.**
19. **Tread safely when he says so** — before a step that touches money data or a security rule, one line of plan, then wait.
20. **The daily Marg routine is his D376.**
21. **STAFF FRIENDLY ALWAYS** (S226): staff never need him for a flow; he steps in only on a problem.
22. **One coherent system** (D380): a spot check anywhere is a count in the main ledger.
23. **Accept, never reject** (D377).
24. **Do not feel pressed for time — do it thoroughly.**
25. **One card, one question; the conclusion first, the workings folded (D383).** A page for him shows one decision at a time; a narration that leads three ways is not a finding. *"I need only your conclusion; the decision metrics expandable."*
26. **One quantity vocabulary (D384):** strips and tabs, pcs for pack 1, IN/OUT in words — never "units", never "(Marg loose N)".
27. **His work must not grow; extra work goes to Amir** — and **a staff sheet carries only what needs that person, with the exact thing to do** (F-339). Lines that agree are never printed. A counter's sheet carries no rupee (D387).
28. **Stock adjustment vouchers are the way to match the count (D388)** — 8 items a voucher; Amir's job is two things: export the ledgers the server asks for and post the vouchers. **Reports the server needs = "export as Excel and upload here — simple, no confusion."**
29. **Analyse HERE.** When a residue needs Marg, ask for the item-ledger EXPORT and read it on the server; do not ask a person a question the data can answer.

---

## PHASE 0 — CONNECTIONS, then verification, then work

1. **Check the connections and prompt him by name:** `D:\Downloads` · `D:\dr-manoj-git` · `F:\ClinicBackup` (never mounts in the device shell; the file-transfer tools reach it; **request `D:\Downloads` if it is not connected — it was not at the S227 open**) · the assistant's browser (F-242 login loop — needs his sign-in).
2. Open `CANONICAL_MANIFEST.md`; **verify every row by md5** (`md5sum -c MD5SUMS_ALL.txt --quiet` from inside `deploy_kits/KB_canon_all/`); halt on a hash mismatch only.
3. Read only Tier 0: manifest · this file · Register v5.76 · Runbook v159 · `OWNER_TODO_LIVE.md`.
4. Open `D:\Downloads\ClaudeCowork\00_INDEX.md`, `03_WORKING_PAPERS\S227\S228_BUILD_BRIEF.md` and `S227_BUILD_BRIEF.md`.
5. **Never run `git` against the mounted repo (F-233 / F-332)** — `ls`/`find` to look; `find -name __pycache__` before a publish; `python3 -B` always.

---

## ⭐ FIRST ACTIONS AT S228 — `S228_BUILD_BRIEF`, in his order

1. **The item-ledger import** — Amir exports Marg's item ledger (Excel) for the items and windows the server names; the server reads it and names the voucher. First four: DISPO SYRINGE NIPRO 3ML · VINTAZ P 4500 INJ (an item merge — F-337) · TYRO BR · ASTOFEN SP. Under one strip → straight to the voucher list.
2. **Amir's board → two jobs**: (a) ledger exports wanted + the upload box (`/finance/stock/page/amir`); (b) STOCK ADJUSTMENT VOUCHERS to match the physical count, 8 a voucher, issue for excess / receive for additions, one Excel per batch; the cleanup, no-movement and orthotics lists collapse into it. Agreeing lines never shown.
3. **Darpan's lists move to the owner's page** (the tranche engine stays).
4. **The owner's LOSS DESK** (D389): tick items; loss at MRP and at cost; high-cost / high-volume on top; an A4 portrait core-data print for Darpan saved on the VPS as the shared copy; recoveries logged.
5. **The spot-count card** on Darpan's page (Hindi): random items, counted, matched live, mismatches flagged to him and the owner.
6. **A8c — pull the VPS deploy clone** after the close's publish: `git -C /root/deploy/repo fetch --depth 1 origin main && git -C /root/deploy/repo reset --hard origin/main` — his one line.

---

## THE BACKLOG POINTER

**`HANDOFF_RUNBOOK_2026-09-06_Session227close_v159.md` §2** — ⭐0 his actions (VINTAZ P write-off tap · a Marg backup · the 12 bills into Marg · the wall-card reprint · the August advances · the S182 tiles word · FINALISE · the delete lists) · ⭐1 the S228 brief (items 1–5 above) → kit C (the nightly Marg audit, the readiness gate, the MRP + salt import, `finance_backup.sh` + `pad_uploads/`) → then S226's list unchanged.

---

## NEXT FREE NUMBERS

**D390 · F-340 · Session 228.**

---

## THE FIVE STORES, AND THE ONE RULE

project knowledge = canon · GitHub = code + `deploy_kits/KB_canon_all/` (**no numbers, F-185**) · `D:\Downloads\ClaudeCowork\` = everything canon excludes · `F:\ClinicBackup\` = frozen mirrors and cold kits, one folder per project · Google Drive = the only phone-readable route, still not set up.

**NO DOCUMENT MAY BE LIVE AND EDITABLE IN TWO STORES** (D202 · F-201). Dated frozen snapshots are exempt. **No canonical document is a delta.** **The manifest WINS on what is current.**

---
*START_HERE_SESSION_228 · generated at the S227 close, 06-Sep-2026.*
