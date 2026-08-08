# CLINIC ESTATE — MASTER APP & SERVICE INVENTORY (reconciled)

**Owner:** Dr. Manoj Agarwal · Bareilly · **Compiled with:** Claude (Clinic Automation project)
**Created:** 07 Aug 2026 · **Version:** v1.7 (Follow-up Tracker grounded — every app verified from source)

**Purpose.** ONE current, reconciled inventory of every app/service across all three
"projects" — Clinic Automation, Website/SEO/Content (clinic-growth), and Personal Health —
built to serve the doctor-portal + manager-portal + single-sign-on design. It reconciles
three sources into one picture.

**Sources reconciled**
1. This project's canon — **KB Register v2.9 (S156)**, HANDOFF_RUNBOOK v94, CANONICAL_MANIFEST
   (Phase-0 hash-verified). *Authoritative for the automation core.*
2. `Clinic_App_Register_v1.md` (Website/SEO project, 07 Aug 2026) — current.
3. `App_Service_Register_v1.md` (07 Aug 2026 file date, **but content "as of Master KB v1.36 /
   Session 63"** — ~93 sessions stale; see §5). Used only for the S63-era baseline.
4. Live repo `drmanoj-clinic-automation` (folder tree pulled + verified this session).
5. Live repo `drmanoj-health-systems` (now **public**) — full source read this session: grounds the
   personal cluster (RxGuard, GutLog, FitLog) + its `CLAUDE.md` conventions.

**Confidence legend**
- **[V]** verified against this project's canon and/or the live repo tree this session.
- **[R]** reported by another project's register (memory-based) — verify with the owning project.
- **[?]** unknown / unconfirmed — flagged for follow-up.

**Hard boundary (all projects):** PHI and staff-financial data never reach cloud, chat, or GitHub.
VPS holds only non-sensitive, internet-reachable services. (F-31 / golden rule.)

---

## 0. The three "projects" — a documentation boundary, not a code boundary

The split into three projects is an organisational convention for *documentation*. Physically,
**the automation repo is effectively a monorepo**: it holds `assetapp/`, `casepack/`, `gutlog/`,
and `gmail-automation/` alongside the automation services **[V]**. So "which project built it"
tells you where the *docs* live, not where the *code* lives.

- **Clinic Automation** — VPS services, Google Apps Script cockpit, call/WABA pipeline, attendance,
  salary ledger, follow-up tracker. Canon = KB Register v2.9 + `sops/`.
- **Website / SEO / Content (clinic growth)** — Asset Register, Surgical Case Pack, Clinic Hub,
  GMB Review Assist, Surgical Estimate, Ayushman finder.
- **Personal Health** — RxGuard, GutLog, Fitlog, plus personal-account Gmail automations.
  Different *trust class*; on the same VPS but no clinic/PHI data.

---

## 1. THE ESTATE AT A GLANCE

| App / service | Host · port/path | Project | Login today | Portal role | Conf |
|---|---|---|---|---|---|
| Callback Dashboard / Call Console ("the cockpit") | Apps Script `/exec?k=` | Automation | DASH_KEY (doctor) / AKEY_ext (staff) | Doctor | V |
| Attendance dashboard | `attendance.dr-manoj.in` :8042 | Automation | cookie | Doctor + Manager | V |
| Staff Ledger + `/salary` engine | `attendance.dr-manoj.in/ledger` :8043 | Automation | user+password (maker/checker) | Doctor (approve) · Manager (entry) | V |
| **Asset Register** | `assets.dr-manoj.in` :8030 | Website/SEO | 2 roles (owner/manager), 3 identities | Doctor + Manager | V (folder) / R (auth) |
| Doctor Portal `/portal` (launcher) | `followup.dr-manoj.in/portal` :8099 | Automation | PIN + device-trust cookie | *is the portal* | V |
| WABA approve | `followup.dr-manoj.in/wa-approve` :8101 | Automation | key gate | Doctor | V |
| WA receiver / send / call-api / call-hook | :8095/:8096/:8097/:8098 | Automation | secret gates | back-end (no UI) | V |
| clinic-followup-receiver | :8100 `/fu-upload` | Automation | FU_UPLOAD_SECRET | back-end | V |
| attlistener (biometric capture) | :8041 | Automation | device-facing, no login | back-end (critical) | V |
| RxGuard | `rx.dr-manoj.in` :8031 | Personal | password + owner-key | Personal cluster (switcher bar) | V |
| GutLog | `health.dr-manoj.in` :8020 | Personal | password + owner-key | Personal cluster (switcher bar) | V |
| FitLog | `fit.dr-manoj.in` :8040 | Personal | password + owner-key | Personal cluster (switcher bar) | V |
| Follow-up Tracker ("the brain") | Local PC :5000 | Automation | local, no login | Clinic Hub | V |
| Vitals & Plan (clinic_writer v28) | Local PC :5057 | Automation | local, no login | Clinic Hub | V |
| Surgical Case Pack | Local PC :5058 | Website/SEO | local, no login | Clinic Hub | V (folder) / R |
| CC Statements → Tally | Local PC :5059 | Automation | local, no login | Clinic Hub | R |
| Clinic Hub (launcher) | Local PC (static + .bat) | shared | none | *is the local hub* | R |
| GMB Review Assist | Local HTML | Website/SEO | none | Clinic Hub card | R |

---

## 2. BY HOST TIER

### 2A · VPS always-on services (Flask · gunicorn · systemd · OpenLiteSpeed proxy)

Host `93.127.195.49` (AlmaLinux 9, CyberPanel/OpenLiteSpeed). All bind `127.0.0.1`, each with its
own port + systemd unit + OLS proxy context. **This is the CURRENT list — it corrects the S63-era
"9 services" of `App_Service_Register` by adding 8030 and 8043.**

| # | systemd unit | Port | Public path | Role | Conf |
|---|---|---|---|---|---|
| 1 | `attlistener.service` | 8041 | — | Secureye biometric punch capture → `punches.csv`. Critical path. | V |
| 2 | `attendance-dashboard.service` | 8042 | `attendance.dr-manoj.in` | Attendance day view + month register | V |
| 3 | `staff-ledger.service` | 8043 | `attendance.dr-manoj.in/ledger` | Ledger (maker/checker) + `/salary` compute/approve. `staff_ledger.py` **v3.1** | V |
| 4 | `wa-receiver.service` | 8095 | `/wa-webhook?key=` | WA inbound → `WA_Inbox` (gate `WA_WEBHOOK_SECRET`) | V |
| 5 | `wa-send-api` | 8096 | `/wa-send` | WA outbound templates + 24h free-text (gate `SEND_API_SECRET`) | V/R |
| 6 | `call-api` | 8097 | `/call` | OBD click-to-call as logged-in agent (gate `CALL_API_SECRET`) | V/R |
| 7 | `call-hook.service` | 8098 | `/mo-callhook` | MyOperator call webhooks → `Call_Durations` (dual-key gate) | V |
| 8 | `clinic-portal.service` | 8099 | `/portal` · `followup.dr-manoj.in` | **Doctor launcher portal**. PIN + device-trust cookie; tiles link to tools. `launcher/portal.py` | V |
| 9 | `clinic-followup-receiver` | 8100 | `/fu-upload`,`/fu-ping` | Receives `Staff_Action_Today.xlsx` from clinic PC (gate `FU_UPLOAD_SECRET`) | V/R |
| 10 | `wa_approve` (nohup, **not yet systemd**) | 8101 | `/wa-approve` | WABA send approval page. 🔴 sends blocked vendor-side (`WABA_SEND_AUTHORIZER_500`) | V |
| 11 | `wa-notifier` | — | — | Polls `WA_Inbox` → ntfy name-only alerts (no web UI) | V |
| 12 | `assetapp.service` (2 workers) | 8030 | `assets.dr-manoj.in` | **Asset Register** — equipment/contracts/staff-doc expiries + doc scanner. `assetapp/app.py` **v1.1.0** | V (folder) / R (detail) |

**Personal-health VPS apps (same box, separate trust class):**
| unit | Port | Public | Role | Conf |
|---|---|---|---|---|
| RxGuard | 8031 | `rx.dr-manoj.in` | Medication-safety review; deterministic rule engine (no LLM in analysis path); 60 molecules, 24 pairwise rules | V |
| GutLog | 8020 | `health.dr-manoj.in` | GI/health logging; Flask+SQLite (`/root/gutlog/health3.db`); v3.2 | V |
| FitLog | 8040 | `fit.dr-manoj.in` | Physical-capacity & recovery engine; deterministic rules; DB `/root/fitlog/fitlog.db`; v1.0.1 | V |

Repo: **`drmanoj-health-systems`** (public). `CLAUDE.md` pins the runtime: **Python 3.9.25** (no PEP 701
f-strings — same-VPS constraint that bit the clinic ledger, F-53), SQLite 3.34.1, Flask 3.1.3, gunicorn
23, `python3 -m gunicorn`, WinSCP delivery, test-before-deploy. Each app: single-file Flask + SQLite +
systemd + OLS proxy, `sqlite3.backup()` nightly (30-day). Auth = login password + separate owner-key
(guards credential changes). The three are cross-linked by a **switcher bar** but hold **independent
logins** — deliberately NOT SSO (single-user, so it was never needed).

`clinic_watchdog.py` guards **11 services** (KB v2.9), including `staff-ledger.service` and — noted
but *not managed by this project* — the owner's `gutlog.service` (Health project). **[V]**

### 2B · VPS scheduled timers (systemd)

| Timer | Schedule (IST) | What it does | Status |
|---|---|---|---|
| `clinic-followup-push` | 22:00 / 07:00 / 11:00 | Builds/pushes day's follow-up list → `Followups_Today` | LIVE [R] |
| `call-recording-archive` | 02:00 | Archive yesterday's recordings to Drive (don't hand-trigger) | LIVE [V] |
| `call-transcription` | 03:00 | Sarvam `saaras:v3` transcription | LIVE [V] |
| `call_verdict` sweep | ~03:40 | Blind AI judge → `Call_Verdicts` | LIVE [V] |
| `flag_investigator` | */30, 09:00–20:00 | Missing-recording detection + self-heal + Lokesh escalation | LIVE [V] |
| `daily_digest` | 11:00 + 21:30 | Morning pulse + full digest | LIVE [V] |
| `clinic-watchdog` | every 5 min | Service watchman (11 services) → ntfy + Gmail | LIVE [V] |
| Daily health report | 08:00 | `clinic_health_report.py` full summary | LIVE [V] |
| `clinic_timer_freshness` | hourly | Timer heartbeat freshness alerts | BUILT, **not armed** [V] |
| assetapp backup | 02:30 | nightly SQLite backup (14-day) | LIVE [R] |
| gutlog backup | 02:15 | nightly DB backup (30-day) | LIVE [R] |

### 2C · Subdomains (all under `.dr-manoj.in` unless noted)

| Subdomain | Serves | Trust class |
|---|---|---|
| `followup.dr-manoj.in` | VPS hub: `/portal`, `/wa-approve`, `/mo-callhook`, `/call`, `/fu-upload` | clinic |
| `attendance.dr-manoj.in` | attendance (:8042) + `/ledger` (:8043) | clinic (staff financial via ledger) |
| `assets.dr-manoj.in` | Asset Register (:8030) | clinic-growth |
| `rx.dr-manoj.in` | RxGuard (:8031) | personal |
| `health.dr-manoj.in` | GutLog (:8020) | personal |
| `fit.dr-manoj.in` | FitLog (:8040) | personal |
| `contact.dr-manoj.in` · `save.dr-manoj.in` | vCard / QR (static) | public |
| `drmanojagarwal.com` | WordPress site (same VPS, separate estate) | public |

### 2D · Google Apps Script — TWO accounts (Google-side, no PHI)

**Clinic account `drmka.ortho@gmail.com`:**

| App | Where | Role | Conf |
|---|---|---|---|
| **Clinic Dashboard / Call Console** ("the cockpit") — **the only user-facing GAS** | `/exec?k=KEY` | Callbacks, click-to-call, WA feed/reply, recordings, follow-up loop, incoming outcomes, escalations. 13 server files + Dashboard.html: `WebApp.gs` (**1,647 lines — matches canon D189/S130, frozen D34**), `Dashboard.html` (3,169 lines), `Callconsole.gs` (1,224), `OutcomeLog.gs` (554), `Health.gs` (428), `Monitor.gs` (324), `Netting.gs` (184), `MyOperator.gs` (177), `Diagnostics.gs` (153), `Sheets.gs` (131), `Main.gs` (107), `CallField.gs` (105), `config.gs` (82). Access: **DASH_KEY**=doctor, **AKEY_ext**=staff | V |
| Daily Clinic Reports (v5) | clinic acct | Trigger `runDaily` → Sheets. Vehicle **trips** (Trip.csv), attendance/absentees, **ICICI bank** ingest, monthly/cumulative recompute; sends **email + WhatsApp digest via MyOperator**. Background, no UI. | V |
| Clinic Accounting Reports | clinic acct | Daily 14:00 + monthly first-Sunday emails. Parses medical/OPD/lab rows, `detectIssues_`, `syncAuditLedger_`, writes detail/summary/pending sheets. Installs its own triggers. Background, no UI. | V |
| UPI Reconciliation | clinic acct | Trigger → compares **logged UPI** ("Accounting details" sheet) vs **settled UPI** (ICICI emails via Daily Clinic Reports), per day/per entity; `maintainOpenExceptions_`, `writeReconTab_`, `sendReconEmail_` on mismatch. Background, no UI. | V |

**Personal account `drmanojkragarwal@gmail.com`** (personal trust class — like the personal VPS cluster; **not** clinic, not portal):

| App | Role | Conf |
|---|---|---|
| Inbox Janitor v2.2 | Daily 7–8am: label/archive/save payment PDFs → **Payment Register**; monthly digest + upcoming renewals; monthly calendar reminders (17-entry renewals array). Background. | V |
| CC Statement Saver (`CC_saver`) | Files credit-card statement PDFs Gmail→Drive, one folder per card. Background. *≠ the local `:5059` CC→Tally app.* **(Corrected: personal, not clinic — was mis-grouped.)** | V |

**Portal takeaway:** only the **cockpit** is user-facing → the single Apps Script portal tile (doctor,
link-based via `?k=`). Every other GAS (both accounts) is invisible back-office — **no portal relevance,
no SSO involvement.**

### 2E · Local PC (Windows, `127.0.0.1`, launched from Clinic Hub)

| App | Port | Path | Role | Conf |
|---|---|---|---|---|
| Follow-up Tracker ("the brain") | 5000 | **C-drive** `followup_tracker\` | Docterz export → dedupe/cap/HTR call list (`processor.py`, D146/D148); **source of follow-up intent**. Also carries: a **push-to-VPS watcher** (`watch_and_push_followups.py` → `:8100`), a local **WABA send layer** (`waba.py`, `send_followups.py`), a **revenue module** (`revenue.py`), a diagnosis normalizer, + test suite. Launch: `START_TRACKER.bat`→`app.py`. Deploy = replace `processor.py`+`app.py` only, never `data\`. Holds local credentials (`.env`, service-account key) — F-31, never read/shared. | V |
| Vitals & Plan (clinic_writer) | 5057 | `D:\clinic_writer\` | `vitals_app.py` + `clinic_writer.py` + `vitals_page.html` **v28** (Tier-2 frozen). Holds patient ledgers (PHI — not read). | V |
| Surgical Case Pack | 5058 | `D:\casepack tool\` | `casepack_app.py` + `casepack_page.html`; one-page pre-surgical paperwork. **Upgrade in progress:** `casepack_app_NEW_lifecycle.py` + `casepack_page_NEW_lifecycle.html` sit alongside the live pair. | V |
| CC Statements → Tally | 5059 | `D:\Scripts\` | `statements_app.py` + `process_statements.py`; CC statements → Tally; auto-runs on hub start. | V |
| Clinic Hub | — | `D:\clinic_hub\` | `clinic_hub.html` + `open_clinic_hub.bat`; local launcher. **PC-only (confirmed not in GitHub).** | V |
| GMB Review Assist | — | `D:\clinic_hub\GMB_Review_Assist_*.html` | Patient-review draft composer; lives inside the Hub folder. | V |
| clinic_salary (data home) | — | `D:\clinic_salary\` | **F-31 salary workbook home** — `Salary_System_2026.xlsx` + S153/S154 SOP/briefing/roster + salary-input reports. Existence only; **contents never read/inventoried.** | V |
| Local git working copy | — | `D:\...\Repos\clinic-automation-2026\` | Local clone/working copy of the automation repo (holds `08_salary_attendance_system.zip` + README). | V |

### 2F · Offline / static / document tools (not hosted apps)

- **Surgical Estimate System** — `Surgical_Estimate_System_v2_1_2.xlsx`; 30 pre-priced procedures, Ayushman cross-ref. Web rebuild is future work. [R]
- **Ayushman package finder** — HTML, link-only, do not modify. [R]
- **Rehab & Nutrition Plan tool** — `plan-tool/rehab_nutrition_plan_v25.html`; offline artifact. [V folder]
- **Fracture Consent Modules** — `Fracture_Consent_Modules_PREVIEW_v7.html`; feeds Case Pack. [R]
- **vCard / QR** — `save.dr-manoj.in`, `contact.dr-manoj.in`. Static. [R]
- **Website** — `drmanojagarwal.com`, WordPress. [R]

---

## 3. AUTH MODELS (the SSO-critical view)

Every *user-facing* app and how it authenticates today. This is the map single sign-on must unify.

| App | Trust class | Auth mechanism today | SSO reachability |
|---|---|---|---|
| Doctor Portal `/portal` | clinic | PIN + device-trust cookie | **anchor** — becomes the auth broker |
| Attendance :8042 | clinic | cookie | **native** — shares `.dr-manoj.in` cookie |
| Staff Ledger / salary :8043 | clinic (financial) | username + password (4 logins, maker/checker) | **native** (VPS Flask) — swap own login for shared cookie |
| Asset Register :8030 | clinic-growth | 2 roles / 3 identities (own login) | **native** (VPS Flask) — swap for shared cookie |
| WABA approve :8101 | clinic | key gate | **native** (VPS Flask) |
| Apps Script cockpit `/exec?k=` | clinic | DASH_KEY / AKEY in URL | **link-only** — Google-hosted, can't take our cookie; tile carries the key |
| RxGuard / GutLog / FitLog | personal | password + owner-key, per app | **switcher-bar cross-links, separate logins** — the "not SSO" reference point; a personal cluster, not on the clinic portals |
| Local PC apps | local | none (LAN) | Clinic Hub launches them; no web SSO |

**SSO conclusion.** Because attendance, ledger, and asset are all **VPS Flask apps on
`.dr-manoj.in` subdomains**, a single login cookie scoped to the parent domain `.dr-manoj.in` is
sent to every one of them. One sign-in at the portal → auto-carried into all VPS apps. The Apps
Script cockpit is the single exception (link-based, not true session).

---

## 4. PORTAL RELEVANCE — doctor vs manager

**Doctor portal** (superset): Apps Script cockpit · Attendance · Staff Ledger **+ /salary approve** ·
Asset Register · WABA approve · (links to local tools when at the clinic PC).

**Manager portal** (subset — the manager runs attendance, assets, and now the ledger): Attendance ·
Asset Register · Staff Ledger **entry only (maker)**.

> **F-31 caution.** The manager portal must **not** expose the salary NET table or the APPROVE &
> LOCK button. Manager = ledger *maker* (enter events); doctor = *checker/approver* + the only one
> who sees salary figures. This is the one permission line to lock before any manager login exists.

All three manager apps are VPS Flask on `.dr-manoj.in` → the manager portal is **100% true-SSO-able**
with no Apps Script exception.

---

## 5. RECONCILIATION — conflicts & staleness found

1. **`App_Service_Register_v1.md` is S63-era.** Dated 07 Aug 2026 but content "as of Master KB v1.36
   / Session 63." Missing the Asset Register (8030), Staff Ledger (8043), the salary stack, and the
   watchdog's growth to 11 services. **Treat as a historical baseline only; KB v2.9 wins.** (Classic
   D188: a filename/date is not provenance.)
2. **Asset app resolved.** The "asset app" = Asset Register, `assets.dr-manoj.in:8030`, `assetapp/`.
   Closes the portal-design unknown.
3. **`clinic-hub/` repo folder not found.** `Clinic_App_Register` says the canonical Clinic Hub copy
   lives in GitHub `clinic-hub/`, but that folder was **not present** in the automation repo tree
   pulled this session. Either it's in another repo or unpushed — **verify** before treating the repo
   as the canonical Hub source.
4. **Monorepo reality.** `assetapp/`, `casepack/`, `gutlog/`, `gmail-automation/` all live in the
   automation repo regardless of "project." Project labels = doc convention.
5. **Personal-apps repo — RESOLVED.** It is **`drmanoj-health-systems`** (now public), a deliberate
   second monorepo: `CLAUDE.md` states clinic and personal systems must not share a repo (different
   lifecycles/sensitivity, cleaner context). ⚠️ But `gutlog/` *also* exists inside the **automation**
   repo — a stray/mirror. Canonical home for personal apps is `drmanoj-health-systems`; the automation
   repo's `gutlog/` should be reconciled (verify it's not a second source of truth).
6. **FitLog — RESOLVED.** `fit.dr-manoj.in`, port 8040, `/root/fitlog/`, v1.0.1, in `drmanoj-health-systems`.

---

## 6. VERIFICATION OWED (to make this fully [V])

- [x] ~~Asset Register auth internals~~ — DONE: `assetapp/app.py` read — Flask session `uid`+epoch, werkzeug hashes, roles owner/manager.
- [x] ~~Local-PC micro-app status~~ — DONE from the D-drive zip: Scripts (5059), casepack (5058, +NEW_lifecycle upgrade), clinic_hub, clinic_writer (5057), clinic_salary (F-31, not read), local repo copy. Follow-up Tracker (5000) not in this zip.
- [x] ~~Locate `clinic-hub/`~~ — RESOLVED: **not in either GitHub repo** (checked both repo dumps + the live automation tarball). Lives only on the PC (`D:\clinic_hub\`) or an unshared third repo; the Website/SEO register's "canonical GitHub `clinic-hub/`" claim is wrong.
- [x] ~~Duplicate `gutlog/`~~ — RESOLVED: confirmed in **both** repos. `drmanoj-health-systems` is canonical (its `CLAUDE.md`); the automation-repo `gutlog/` is a stray copy to remove.
- [x] ~~Personal-apps repo + FitLog~~ — DONE: `drmanoj-health-systems` (public); FitLog `fit.dr-manoj.in`:8040.
- [x] ~~Apps Script projects~~ — DONE: cockpit + DailyClinicReports + Accounting + CC_saver read from source (clinic acct `drmka.ortho@gmail.com`). Cockpit `WebApp.gs` line-count matches canon.
- [x] ~~Inbox Janitor + CC_saver~~ — DONE: both grounded, both **personal** acct `drmanojkragarwal@gmail.com` (CC_saver was mis-grouped as clinic — corrected).
- [x] ~~UPI Reconciliation~~ — DONE: clinic acct; logged-vs-ICICI-settled recon, emails mismatches. Background.
- [x] ~~Confirm S156 push landed for `staff_ledger/`~~ — CONFIRMED: `staff_ledger/staff_ledger.py` is in the live repo (pulled directly). ⚠️ **Note:** the owner's `drmanoj-clinic-automation` **JSON repo-dump is partial** — it omits `staff_ledger`, `wa-diagnostics`, `revenue-reconciliation`, `plan-tool` (export tool truncated; includes the binary `attendance.zip`). Use the **live repo**, not that dump, as the automation source of truth.

---

## 7. QUICK REFERENCE

**VPS:** `93.127.195.49` · `followup.dr-manoj.in` · AlmaLinux 9 · CyberPanel/OpenLiteSpeed · work dir
`/root/wa` · venv `/root/wa/venv/bin/python3` · secrets `/root/wa/.env` (chmod 600) · TZ Asia/Kolkata.
**Ports (VPS):** 8020 GutLog · 8030 Asset · 8031 RxGuard · 8040 FitLog · 8041 attlistener · 8042 attendance ·
8043 ledger · 8095 wa-receiver · 8096 wa-send · 8097 call-api · 8098 call-hook · 8099 portal ·
8100 fu-receiver · 8101 wa-approve.
**Ports (local PC):** 5000 tracker · 5057 vitals · 5058 casepack · 5059 statements.
**Repos:** `drmanoj-clinic-automation` (clinic monorepo) · `drmanoj-health-systems` (personal, public) — deliberately split (`CLAUDE.md`). Both via GitHub Desktop.
**Deploy pattern:** replace one code file → `systemctl restart` → verify. Never touch `data\`,
`assets.db`, `uploads/`, salary/staff files.

---

*End of Master Estate Inventory v1. Supersedes the S63-era `App_Service_Register_v1` for the
automation core and folds in `Clinic_App_Register_v1`. Bump the version/date on any change; keep the
canonical copy wherever the portal build lives.*
