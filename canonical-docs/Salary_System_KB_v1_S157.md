# SALARY SYSTEM KB — Staff Ledger + Backend Salary Automation (v1 · S157)

**Owner:** Dr. Manoj Agarwal · Bareilly · **With:** Claude (Clinic Automation) · **07 Aug 2026**
**Status:** reference KB for a LIVE, evolving system (not frozen). Wholesome single reference for the
salary/ledger stack — consolidates what was scattered across KB Register v2.9, Archive v1.8, Runbook v94.

> **🔒 F-31 — read first.** This KB documents the **system** (architecture, roles, decisions, policy
> rates, code versions). It contains **no individual staff figures** — salaries, deductions, balances,
> loan amounts, or per-person data live ONLY on the VPS (`staff_master.csv`, `users.json`, the ledger
> DB, salary CSV/HTML, the workbook) and must never enter repo, KB, or chat.

**Provenance.** Compiled from this project's canon (Register v2.9, Archive v1.8, Runbook v94, manifest)
plus a direct read of `staff_ledger.py`'s auth/role code this session (S157). Versions/hashes are the
Register-pinned live values.

---

## 1. What it is

The clinic's **staff-money system**: a maker-checker **ledger** plus a backend **salary engine**, built
across Sessions 154→156 (decisions **D257 → D258 → D259**). Live at
`https://attendance.dr-manoj.in/ledger`. It replaces the manual Excel salary workbook, which is now
**read-only** and retires after one clean reconciled month.

**Two cooperating layers — they meet only through files, never through logic:**

1. **Attendance report layer** — `att_month_report.py` (an *additive* layer on the frozen attendance
   core; imports `att_core` so the engine and the report can never disagree). Owns **all attendance
   policy math**. Emits monthly output files (a close CSV + an A4 HTML report).
2. **Staff Ledger + salary engine** — `staff_ledger.py`. Owns **money assembly** (ledger events, fines,
   loans, adjustments) and the `/salary` engine, which reads the attendance report's **output files as
   its interface** and produces the final NET table.

> **Core invariant:** the salary engine reads the report's OUTPUTS, never re-derives attendance policy.
> A single shared `month_adjustments()` rule-set guarantees the close CSV and the salary table can never
> disagree.

---

## 2. Live components (current pins)

| Component | Where | Pin |
|---|---|---|
| `staff_ledger.py` **v3.1** | VPS `/root/staff_ledger/`; `staff-ledger.service`; gunicorn `127.0.0.1:8043`; OLS `/ledger` context | md5 `8bcf1b2d296786717437db672fb29b05`, selftest **184** |
| `att_month_report.py` **v2.5** | VPS attendance folder (additive report layer) | md5 `e64cad19d135618dec1413553e6bdc80` |
| `staff_master.csv` | VPS only — roster + rates (**F-31**) | not pinned here (data) |
| `users.json` | VPS `/root/staff_ledger/` — logins + roles, `0o600` (**F-31**) | — |
| Monthly outputs | `salary_final_<month>.csv` + `salary_final_<month>.html` (frozen at approve) | per-month |
| `clinic_watchdog.py` | guards `staff-ledger.service` (11 services total) | md5 `01ca6591a74ec8009bf9748fb7f480c2` |
| Workbook (retiring) | VPS `/root/clinic_salary/` — `Salary_System_2026.xlsx` (**F-31**) | — |

**OLS wiring:** the attendance vhost gained `extprocessor ledger8043` + `context /ledger` (guarded edit;
backup `/root/vhost.conf.BACKUP_S154`); attendance serves 302, `/ledger` serves 200.

---

## 3. Maker-checker model (D257)

- **Roles:** `maker_full` (Shavez), `maker_limited` (Alisha), `checker` (the doctors).
- **`ROLE_CATS` = explicit allow-lists per role** — never "all categories" (this was the **F-50** fix).
- **Makers** enter events → **PENDING**. **Checkers** approve (or direct-enter, which auto-approves).
- **Ad-hoc fines** are doctor-only, with mandatory narration.
- **Corrections are append-only + contra-only** — nothing is ever deleted; a mistake is reversed by a
  contra pair that nets to zero and stays on the record. Self-entries are flagged.
- **Policy rates (D257, per day):** ₹20 / ₹20 / ₹200 / ₹100 for the respective fine/duty categories
  (exact category mapping in Register D257). *These are policy, not staff data.*

---

## 4. Advances / loans (D250, D258)

- Interest-bearing advances (loans) are **checker-only** to issue; declining balance; monthly instalment
  + interest; a **skipped month recovers nothing** (accounting-honest).
- Loan payout is **excluded** from the salary summary (it's a balance-sheet movement, not pay).
- **D258 executed:** Darpan's loan was migrated live into the ledger, rupee-verified; the workbook's loan
  machinery was retired; canonical workbook home moved to VPS `/root/clinic_salary/`.

---

## 5. The salary engine (D259) — the backend automation

`/salary` (checker-only) does the whole month end-to-end, with no manual Excel entry:

1. **Reads** `att_month_report`'s output files as the interface (never re-computes attendance policy).
2. **Pulls the paper loops on-screen:** informed-flags; EARLY_BIG (genuine at the report's OWN ₹, and
   **fail-loud if the number drifts**); OT approval (capped at candidate, default 0); outstation
   (Darpan excess-fine recompute).
3. **Assembles** the ledger's closed adjustments + each base salary → the **NET table** (nearest rupee).
4. **APPROVE & LOCK** (with a confirm) → appends one `SALARY_PAID` row per staff + writes
   `salary_final_<month>.csv` + freezes the full report `salary_final_<month>.html` (which is the
   owner's vetted attendance grid HTML with a salary section spliced in).
5. **Input-token anti-drift:** an md5 over every byte that fed the numbers is captured; any drift between
   preview and the APPROVE press **refuses** the approval.
6. **A locked month is frozen, never recomputed.** A wrong figure is fixed by a **next-month adjustment
   entry** — same family as "a loan repayment is never typed."

---

## 6. UI safety (F-51)

A one-tap button that appends real money rows **must confirm first**. Implemented: contra 2-step confirm
(step 1 appends nothing), skip confirm, void-pair greying, statement month headers. **Append-only + a
void-pair display beats a delete button** — the screen stays clean and no rupee is ever erasable.

---

## 7. Authentication (read from source, S157)

- **Flask session.** Per-app secret in `/root/staff_ledger/secret_key` (random 32-byte hex).
- `session["u"]` = username; the role is looked up in `users.json`.
- Route prefix `/ledger`; login at `/ledger/login` (username + password; swappable password logins).
- **`/salary` is checker-only in code** → a manager (maker) cannot reach salary figures or the APPROVE
  action even by typing the URL. **This is the F-31 line, enforced by the existing role guard** — relevant
  to the planned manager portal (which will map role `manager` → ledger `maker`).

---

## 8. Deploy discipline

WinSCP upload → **md5 verify on the VPS** → **compile + run all selftests on the VPS's Python generation
(3.11 via `uv`)** → restart the service. The wrong-Python lesson (**F-53**): a green compile/selftest on a
newer Python than the target proves nothing. Build from the **live VPS copy** verified by md5, never from
the repo mirror assumed current (**F-52**, reinforcing D160).

---

## 9. Data & the F-31 fence

- **Never in repo/KB/chat:** `staff_master.csv`, `users.json`, the ledger DB, `salary_final_*.csv/html`,
  the workbook. All live only on the VPS. `.gitignore` blankets `*.csv` (**F-49**).
- Salary-bearing generated files are git-ignored or produced outside the tree.
- Printing from salary-bearing files is **whitelist-only** — never mask-by-exclusion (**F-46**).

---

## 10. Decisions & findings index (full text in Archive)

- **D250** Darpan loan system · **D255** staff-management design (ledger/advances/appraisal/maker-checker)
  · **D257** maker-checker built · **D258** Darpan migration + workbook demotion · **D259** full backend
  salary automation.
- **F-46** whitelist-only salary printing · **F-49** salary CSV in git tree (gitignore gate) · **F-50**
  checker allow-lists · **F-51** one-tap confirm · **F-52** repo stale vs live · **F-53** wrong-Python compile.

---

## 11. Version lineage

`staff_ledger.py`: **v1.2** (S154, D257 maker-checker) → **v2.4** (S155, D258 statement view + loan engine
+ Darpan migration, selftest 123) → **v3.1** (S156, D259 `/salary` engine + F-51 batch + salary report,
selftest 184, `8bcf1b2d…`).

---

## 12. Open items

- **July salary reconciliation (owner):** on `/salary/report?m=2026-07`, compare each NET vs actually-paid.
  A clean verdict officially demotes the workbook to read-only. **July never gets an APPROVE press** (it
  was paid via the workbook).
- **August = first REAL approval** (~Sep 01–09): enter all August events → `close 2026-08` → preview →
  APPROVE & LOCK.
- **Repo commit** owed: ledger v3.1 + watchdog + canonical-docs mirror (owner reports done from a prior
  git kit — verify against the live repo). Ledger DATA / workbook / salary CSV+HTML: **NEVER** (F-31).

---

## 13. Related references

- **`Attendance_System_Dossier_v1_2_S153.md`** — the attendance-report half (`att_month_report` additive
  layer over the frozen 10-file attendance core).
- **KB Register v2.9 / KB History Archive v1.8** — current state + full history / decision text.
- **`Clinic_Portal_SSO_Architecture_v1.md`** — the planned portals; the ledger's role guard is the F-31
  enforcement point the manager portal relies on.

---

*End — Salary System KB v1 (S157). Living system; bump on any `staff_ledger.py` / `att_month_report.py`
change. Register this KB in `CANONICAL_MANIFEST.md` (Tier 1) + a Register pointer at the next EOS.*
