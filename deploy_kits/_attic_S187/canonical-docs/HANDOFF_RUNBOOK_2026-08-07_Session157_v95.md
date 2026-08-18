# HANDOFF RUNBOOK — 2026-08-07 — Session 157 — v95

## §0 — WHAT HAPPENED (S157, EOS-light — documentation & design only; NO live code, config, trigger, or property touched; no GitHub commit)

1. **Phase 0 caught a real gap.** All 22 canonical rows hash-verified, but **`KB_Register` v2.9 was absent from project knowledge** (the S156 doc-swap had missed it while every other S156 doc landed). Halted per D172/D188; owner re-uploaded; md5 matched `a5b38555f42aa4f2556ee1a1550b6c20`; verification then fully green. Absence proven by exhaustion (D201).
2. **Pivoted from the July-reconciliation backlog to a full estate-mapping + portal/SSO design push** at the owner's direction. Over the session the owner fed the **entire estate**: the two crude cross-project registers, all six Apps Script exports (4 clinic + 2 personal accounts), both GitHub repo JSON dumps, the D-drive apps zip, and the C-drive follow-up-tracker zip.
3. **`Clinic_Estate_Master_Inventory_v1.md` (v1.7) produced** — the complete reconciled cross-project estate (15 VPS services, 11 timers, 6 GAS projects across two Google accounts, both repos, every local PC app), every clinic-relevant row grounded from source. Supersedes the **S63-era** `App_Service_Register` for the automation core.
4. **Auth code of the four portal apps read from the repo** (portal / attendance / ledger / asset): four different schemes, no shared secret or identity — so true SSO needs a broker, not a shared cookie alone. The ledger's `/salary` is already checker-only (the F-31 line is enforced in code).
5. **Design docs produced:** `Clinic_Portal_SSO_Architecture_v1.md` (SSO broker + a ~15-line shared verify-shim per app; `.dr-manoj.in` signed cookie; each app's own login kept as fallback) and `Clinic_Portal_Build_Plan_v1_S157.md` (doctor + manager tile rosters; per-app selection table; **local apps = a PC-only, live-detected group that absorbs the Clinic Hub**; the cockpit is the only GAS tile).
6. **`Salary_System_KB_v1_S157.md` produced** — a new Tier-1 reference consolidating the Staff Ledger + backend salary automation (F-31-safe; system only, no figures).
7. **Cold kit built + sanitized:** `DrManoj_Estate_ColdKit_S157.zip` (all session docs + owner artifacts). Sanitization **caught and removed** patient consent files (`case_archive/`), patient plan PDFs (`plan_archive/`), the tracker's patient `data/` + a `.secret_key`, F-31 salary files, and a **live GCP service-account key** — the kit ships code/structure only.

Findings: **F-54** (App_Service_Register wore a 7-Aug date over S63-era content — a provenance trap), **F-55** (the automation GitHub JSON repo-dump is partial — the export truncated, missing `staff_ledger`, `wa-diagnostics`, `revenue-reconciliation`, `plan-tool`), **F-56** (uploaded PC zips carried live credentials + PHI + F-31 salary data even after "most data files" were deleted; sanitized out of the kit — **rotate the service-account key**). Resolutions: `clinic-hub` is in **neither** repo (PC-only); `gutlog` is duplicated in **both** repos (health-systems canonical). Decisions **D260–D263** minted. Backlog #3 (S156 repo push) reported **done** by the owner from the previous chat's git kit. No live-system fault; no incident. Notion absent a seventh session.

## §1 — MENTAL MODELS (delta only)

- **The estate is one system across three hosts; the "projects" are a documentation boundary, not a code one.** The automation repo is effectively a monorepo (it holds `assetapp`, `casepack`, `gutlog`, `gmail-automation`).
- **True SSO ≠ a shared cookie alone.** A `.dr-manoj.in` cookie *reaches* every subdomain, but each app must *trust and verify* it. With four different auth schemes live, SSO = a broker (owns login + roles, issues one signed cookie) + a shared verify-shim per app, with each app's own login kept as the fallback.
- **Local apps are `localhost` + PHI — they can't and shouldn't be served remotely.** They join the portal as a "Clinic PC only" group whose tiles work when the portal is opened on the clinic PC and are hidden otherwise. This lets the portal absorb the Clinic Hub without exposing anything.
- **A register, a repo-dump, or a filename is not provenance (D188, reinforced twice).** The S63 register wore a current date; the JSON repo-dump silently omitted four live folders. Build from the live repo/source, verified by hash — never the artefact that merely *looks* current.
- **An uploaded "code" zip can still carry secrets + PHI + F-31 data** after the obvious data files are deleted (F-56). Sanitize (whole data/output/archive directories, secret files, keys) before aggregating anything for reuse.

## §2 — LIVE BACKLOG (ordered) — owner set the top two for S158

1. **Ledger fine-tuning tasks (owner to detail)** — top priority next session.
2. **Portal build with SSO** — start **step 1 (the broker)** per `Clinic_Portal_SSO_Architecture_v1` + `Clinic_Portal_Build_Plan_v1`. Four open portal decisions to settle first: manager login (shared vs named Shavez/Alisha) · which report-Sheet tiles · absorb the Hub (recommended) · one "Personal" link-out or not.
3. **July salary reconciliation (owner carry):** `/salary/report?m=2026-07`, each NET vs actually-paid; clean verdict demotes the workbook to read-only. **No APPROVE for July, ever.**
4. **Rotate the Google service-account key (F-56 — now urgent; it was in the tracker zip)** + the overdue CALLHOOK / key rotations.
5. **Repo commit:** confirm the S156 git-kit push actually landed (owner reports done — verify against live repo); then commit the four new S157 docs into `canonical-docs/`. Ledger DATA / workbook / salary CSV+HTML: **NEVER** (F-31).
6. **August salary run (~Sep 01–09)** — first REAL APPROVE & LOCK.
7. `wa_approve` systemd verify · WABA sends blocked on Lokesh · **Notion catch-up S151–S157** (seven sessions) · clinic_writer Hindi spellings (Tier-2 waiver).
8. Parked: D255 appraisal · Insight Harvest (D241) · D223 gist tile · Docterz (D243).

## §3 — REPO

No live code this session. To commit next session: the four new S157 docs → `canonical-docs/` (`Clinic_Estate_Master_Inventory_v1`, `Clinic_Portal_SSO_Architecture_v1`, `Clinic_Portal_Build_Plan_v1_S157`, `Salary_System_KB_v1_S157`) + the S156 code push (verify it landed). The cold kit is a **local backup**, not committed (contains sanitized code but is a handoff artifact). `gutlog.service` remains the owner's separate Health project.

*Runbook v95 supersedes v94. Next session: 158. Next free: D264 · F-57.*
