# HANDOFF RUNBOOK — 2026-08-07 — Session 156 — v94

## §0 — WHAT HAPPENED (S156, FULL EOS — backend salary automation D259 built + live; F-51 UI safety; watchdog guards staff-ledger; two delivery-gate findings F-52/F-53)

1. **Opened on an owner incident that shaped the build.** The owner had tapped the red **contra** button **4 times** on the pre-migration Shivani test fine (no confirmation on the button) and worried Darpan showed "skipped". From a phone screenshot: **Darpan is CORRECT** — the "skipped" row is the legitimate **2026-04** skip at the top of the list; July applied normally (₹1,000 interest + ₹4,000 instalment, loan **179,000**), all matching S155 → nothing logged. **Shivani** fixed the append-only way: fine + first contra net to zero and stay; the **3 extra contras** each got a reversal ("duplicate contra - reversed") → her line nets to zero across 8 entries. Ignore her line entering July salary. The four-tap became **F-51**.
2. **Design pass (D259, owner-ruled 5 decisions):** approval **on-screen** (doctor login + confirm), **master sheet only** (no per-staff payslips), approved salary **appears as a statement line**, workbook **read-only now / retires after one clean month**, net **nearest rupee**. Owner handed over his vetted month-salary artefact and directed the salary report BE that design.
3. **Built `staff_ledger.py` v2.4 → v3.1** (five internal versions, all selftested). **v3.0:** `/salary` engine — reads `att_month_report.py` OUTPUT FILES as the interface (never re-derives policy math; shared `month_adjustments()` = one rule-set for close CSV + salary); pulls the 3 paper loops on-screen (informed flags, EARLY_BIG genuine at the report's OWN ₹ / fail-loud on drift, OT approval capped-at-candidate default 0, Darpan outstation → recomputes excess fine); **APPROVE & LOCK** (confirm) → `SALARY_PAID` system rows + `salary_final_<month>.csv`; input-token guard refuses recompute drift; corrections are next-month adjustments. **F-51 batch:** contra 2-step confirm (step 1 appends nothing), skip confirm, void-pair greying, statement month headers. **v3.1:** salary REPORT = the vetted attendance HTML **verbatim** + a spliced FINAL SALARY section (printable table + collapsible per-staff breakdowns; PREVIEW/LOCKED banner; frozen to `salary_final_<month>.html` at approve). Selftest **123 → 184**; ~9 mutation probes, all killed.
4. **Watchdog:** `clinic_watchdog.py` gained `staff-ledger.service`. Repo copy hash-MISMATCHED live → **F-52**: live guards **`gutlog.service`** (owner's separate Health project) that neither repo nor canon knew; installing the repo build would have silently dropped it. Rebuilt on the TRUE live copy (`096aba39…`) → `01ca6591…`, 11 services, hand-run 11/11 up.
5. **Install drama → F-53.** v3.1 first shipped `06bf03cb…` — compiled + 184-selftested on the sandbox's **Python 3.12** but died on the VPS's older Python: `SyntaxError: f-string expression part cannot include a backslash`. Fixed (backslash lifted out of the f-string; whole-file swept — none left) and **re-proven by compiling + running all 184 checks under Python 3.11** (`uv`). Final **`8bcf1b2d296786717437db672fb29b05`** installed, md5-exact, 184/184 on the VPS, restarted. The bad upload never endangered the service (a syntax-error file can't start; v3.0 kept running; watchdog would have caught a death in 5 min).
6. **Verified live:** ledger v3.1 `8bcf1b2d…` (VPS md5 + 184 selftest + restart); watchdog `01ca6591…` (VPS md5 + 11/11). **July page rendered on the owner's phone** (12 staff, preview total ₹107,447; Darpan's ₹5,000 loan folded in; Shivani ₹1 low exactly as predicted — test fine July / reversal August). **July rupee-by-rupee reconciliation vs actually-paid: OPEN (owner carry).** July never gets an APPROVE press (already paid via workbook); its clean reconciliation officially demotes the workbook to read-only.

Fault codes: **F-51** (raised + fixed), **F-52**, **F-53**. Decision: **D259** (minted + executed). No incident report (no live-system fault; the install syntax error was caught pre-service). Notion absent a sixth session.

## §1 — MENTAL MODELS (delta only)

- **The salary engine reads the attendance report's OUTPUTS, never its logic.** att_month_report owns all attendance policy math; the ledger owns money assembly; they meet only through CSV files. One shared `month_adjustments()` guarantees the close CSV and the salary table can never disagree.
- **A locked month is frozen, not re-computed.** Approval carries an input-token (md5 over every byte that fed the numbers); any drift between preview and press refuses the approval. A wrong salary is fixed NEXT month by an adjustment entry — accounting-honest, same family as "repayment is never typed."
- **The salary report is not a new artefact — it is the owner's vetted attendance HTML with a section spliced in.** Never rebuild his grid/legends/collapsibles; read them verbatim and append.
- **Build from the live VPS copy of any operational script, verified by md5 — never from the repo mirror assumed current** (F-52; reinforces D160). The mirror is a publish target, not a source.
- **A green compile/selftest on the wrong Python is not green** (F-53). Every VPS-bound Python file is compiled AND selftested against the VPS's Python generation (3.11 via `uv`) before delivery. Kin of "a check that cannot fail is not a check."
- **A one-tap button that appends real money rows must confirm first** (F-51). Append-only + a void-pair display beats a delete button: the screen stays clean, no rupee becomes erasable.

## §2 — LIVE BACKLOG (ordered)

1. **July salary reconciliation (owner):** on `/salary/report?m=2026-07`, compare each NET vs actually-paid. Verdict "all match" (or "all match except Shivani ₹1") officially demotes the workbook to read-only. **No APPROVE press for July, ever.**
2. **August salary run (~Sep 01–09) — first REAL approval:** enter all August ledger events → Salary → informed flags → EARLY_BIG/OT/outstation rulings → run attendance report → `close 2026-08` (contains Darpan's next ₹5,000 + all August events + the Shivani contra netting) → preview → **APPROVE & LOCK**. Frozen report + CSV land automatically.
3. **Repo commit owed (one GitHub Desktop session):** `staff_ledger/staff_ledger.py` v3.1 `8bcf1b2d296786717437db672fb29b05` · `clinic_watchdog.py` `01ca6591a74ec8009bf9748fb7f480c2` (live-verified; repo two versions stale on the ledger) · canonical-docs mirror refresh (S155 **and** S156 sets now behind + ~15 root strays). `.gitignore` still gates any `*.csv`. Ledger DATA / workbook / salary CSVs & HTML: **NEVER** (F-31).
4. **Tiny cleanup (owner):** `rm /root/watchdog_live_copy.py` if not already done.
5. First-real-entries onboarding: Shavez & Alisha maker briefing + passwords (carried).
6. `wa_approve` systemd — verify `systemctl status` first (record conflict) — carried.
7. Overdue key rotations — carried. 8. WABA sends blocked on Lokesh — carried.
9. **Notion catch-up S151–S156** (six sessions).
10. clinic_writer Hindi spellings — carried (Tier-2 waiver).
11. Parked: D255 appraisal, Insight Harvest D241, D223 gist tile, Docterz (D243).

## §3 — REPO

Commits owed (one session): `staff_ledger/staff_ledger.py` v3.1 `8bcf1b2d…` · `clinic_watchdog.py` `01ca6591…` · `canonical-docs/` refresh (Register v2.9, Archive v1.8, Runbook v94, START_HERE_157, manifest; superseded strays → `archive/`). Ledger DATA, workbook, salary CSV/HTML: NEVER (F-31). **gutlog.service** is the owner's separate Health project — the watchdog guards it but this project does not manage it.

*Runbook v94 supersedes v93. Next session: 157. Next free: D260 · F-54.*
