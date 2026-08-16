# START HERE — Session 183

Hi Claude. Continuing my clinic-automation project (**Session 183**).
I'm Dr. Manoj Agarwal, orthopaedic surgeon, Advanced Orthopaedic Surgery Centre, Bareilly.
Solo practice, older Hindi-first semi-urban patients.

*(Session-specific entry point regenerated at the S182 close. The evergreen procedure is
`START_HERE_PROMPT_v5` = this project's custom instructions; follow it. This file carries only the
Phase-0 pointers current as of S182 and the S183 top task.)*

**Working protocol:** plain language · ONE step at a time, wait for explicit confirmation · full-file
replacements · ALL-CAPS = urgent · mask patient numbers to last-4, never print secrets · nothing live
rebuilt without explicit OK, manual workflow stays the fallback · build/test offline, **rehearse the
installer against a throwaway target**, then install via the **D317 kit chain** (owner: one
double-click + one pasted command) · the asset and finance apps use system `/usr/bin/python3` (F-53);
`/root/wa` scripts and the **portal's gunicorn** use `/root/wa/venv/bin/python3`.

**Before you say hello:** connect **Downloads** and **`D:\dr-manoj-git`** in the picker. That lets the
assistant stage kits straight into `deploy_kits\<KIT>\` and sweep Downloads at close (S181 addendum).

---

## Phase 0 — do this FIRST (verification before work)

**One command now does the whole document check, definitively:**

```
cd /tmp && rm -rf kbv && git clone --depth 1 -q \
  https://github.com/manoj-clinic-automation/drmanoj-clinic-automation.git kbv \
  && cd kbv/deploy_kits/KB_canon_all && md5sum -c MD5SUMS_ALL.txt
```

1. Open **`CANONICAL_MANIFEST.md`**. STATUS should read **current at S182**.
2. Verify every row by md5. **A hash verdict is only ever pronounced on bytes delivered as a FILE**
   (git clone, or `project_read` returning a file path). Re-keyed inline text may corroborate, never
   convict or acquit — that rule exists because re-keying produced a **false red** at S182.
   The three **D316 CLOSED-AS-LOST rows do NOT halt**.
3. Read into context only **Tier 0**: the manifest, this file, **KB Register v5.4**,
   **HANDOFF_RUNBOOK v116**, any open incident (none open). Tier 1 on demand.
4. Confirm, then ask which backlog item to start (Runbook §2).

> ⚠ **Phase 0 does NOT verify live code (F-97).** The Register's live-file md5s are checked by
> nothing, and one was stale by two sessions at S182. **Before replacing any live file whole, read its
> md5 off the box and build on that** — never on the Register pin or the repo copy, which can agree
> with each other and both be wrong.

## Where the truth lives
- **`CANONICAL_MANIFEST.md`** — doc set, tiers, hashes. WINS on "what is canonical/current." (S182)
- **KB Register v5.4** — live-file table (portal.py pin **corrected**), decisions through **D320**,
  findings through **F-99**.
- **KB History Archive v1.30** — §S182 is the last section (pure append).
- **HANDOFF_RUNBOOK v116** — §0 what happened · §1 mental models · §2 backlog · §3 install discipline.
- **Fault_Action_Register v2.18** — CURRENT (F-96…F-99 in §7.1).
- **KB_Asset_Register v1.11.0-R** — CURRENT (the D316 reconstruction).

## ⭐ S183 TOP TASK — the Marg April→August backfill
**(a) A v2 driver** doing BOTH stores per day: `ingest_day` → `sale_item` **and**
`finance_returns.load_lines` → `sale_line_item`. The sale-return pipeline needs the drug lines;
`marg_backfill.py` (placed at S182) writes bills only.
**(b) The `marg_export` column map + activation.** Live state: source id=2, `active=0`, **zero column
map rows**. Map onto the parser's real headers — `bill_date · bill_no · clinic_id · patient_name ·
phone_last4 · description · amount · mode` — **not** the selftest's display names (`"Bill No"`,
`"Customer"`, `"Net Amt"`), which would read zero rows and report success.
**(c) The fortnight chunks**, 1 Apr → 15 Aug, ~10 Marg exports with item detail. Each must end in a
GRAND TOTAL row; the parser refuses truncated files.

**Why this is safe:** filed days run **1 Apr → 13 Aug (121 days, legacy_sheet)**, so 1 April is exactly
where the data begins — and **`sale_item` = 0, `sale_line_item` = 0**, so nothing is superseded.

**Owner decisions waiting:** the Docterz reception mode-selection fix (F-91) · Razorpay + ICICI MIS
auto-forwards · lab module (parked) · **ask Darpan about 11 and 14 August** — both 100% cash across 48
bills (₹38,355) against 40–76% on every other day, F-91's shape in the pharmacy.

**Cold-kit count: 2 of 3–5** (F-89 — checked at every close).

**Connected sources:** Google Drive · Gmail · Notion · GitHub (`drmanoj-clinic-automation`,
**PUBLIC by owner ruling D320** — no PHI-bearing artefact may enter it) · ClickUp parked (D17).
Patient data is NOT in this project.

**Next free: D321 · F-100 · A-D25 · Session 183.**

*START_HERE_SESSION_183 — regenerated at the S182 close. Supersedes START_HERE_SESSION_182.*
