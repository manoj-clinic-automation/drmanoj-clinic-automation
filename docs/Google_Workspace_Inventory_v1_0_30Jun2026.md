# Google Workspace Inventory
## Advanced Orthopaedic Surgery Centre, Bareilly
**Account: drmka.ortho@gmail.com**
**Captured: 30 June 2026 · Session 18**
**Purpose: Auto-inventory — reference this instead of searching again**

---

## 1. Apps Script Projects — Complete Register

| # | Project Name | Last Modified | Active Triggers | Status | Script ID |
|---|---|---|---|---|---|
| 1 | **Clinic Callback Tracker** | Jun 29, 2026 | **13** | 🟢 LIVE — primary dashboard | `148sj-FT2tVmNsCdGfz99iSK4_aEbulEpoSAAeYGxIZLuovJBMpLY8CiS` |
| 2 | **UPI Reconciliation** | Jun 24, 2026 | **1** | 🟢 LIVE — daily UPI recon | `1DPLCtvmgLrMjMdzNK8YrIHfkmF6-oJWQOuHnrGoylkG6rSyL-cNAyTHN` |
| 3 | **Untitled project** | Jun 16, 2026 | 0 | 🔴 DORMANT — no triggers | `1bObvgMiEXHv0iX_R-hg5ajrJlhTpkn9vQyb4RevTrwL-obdLDunycIff` |
| 4 | **DailyClinicReports** ⭐ | Jun 15, 2026 | **1** | 🟢 LIVE — daily `runDaily` | `1WFQrMhcDwiaTA2IHaUR8rk5dTWmvKxGs_iL8YcFZhESGCMaBgPkyTOz9` |
| 5 | **Clinic Accounting Reports** | Jun 9, 2026 | **1** | 🟢 LIVE — daily `runDailyReport` | `1pjacHFl_A41CmdVrM6ex37xzqbaGe19uleBG9Osv9mDseTgcoP8S3AcI` |
| 6 | **DailyClinicReports** (old) | Jun 7, 2026 | 0 | 🔴 DORMANT — older version | `1_WV50I9PT2l3vaKAAkaLikvFGqageeH4Hg28l2FtgByPczrfRaU-WycN` |
| 7 | **Untitled project** (old) | Jun 7, 2026 | 0 | 🔴 DORMANT — no triggers | `1xIoAcUXcQ31LVO7trqxmYnwLJCkvfB1xy6mN5uh2cRtVVRuAua-BVCnO` |
| 8 | **Daily Clinic Reports** (old) | Jun 7, 2026 | 0 | 🔴 DORMANT — no triggers | `1dF9dQ3-L8bhevLJ0wcbsaxv0GxNLujgm3GFYqznIc5nkjh0oZmA2eS7T` |

---

## 2. Active Projects — Detailed

### 2.1 Clinic Callback Tracker (PRIMARY — Session work lives here)
- **Files (11):** `appsscript.json` · `config.gs` · `MyOperator.gs` · `Netting.gs` · `Sheets.gs` · `Main.gs` · `Monitor.gs` · `CallField.gs.gs` · `WebApp.gs` · `Dashboard.html` · `Probe.gs.gs`
- **Linked Sheet:** Clinic Callback Tracker (`1USjArkqIdrE9hIqerghms76STatM5XTbSW_a9I3klo0`)
- **Deployment:** Web app `/exec?k=KEY` (build v17.1 · inbound)
- **13 Triggers (all Time-based, all 0% error):**
  - `runIntradayDigest` × 5 (multiple hourly slots)
  - `rebuildCallFeed` × 1 (~21:30 daily)
  - `runSummaryEmail` × 2
  - `sendFollowupSummary` × 1
  - `runMorningReport` × 1
  - `runIntradayDigest` × 3 (additional slots)
- **Last run:** Jun 29, 2026

### 2.2 UPI Reconciliation
- **Purpose:** Reconciles logged UPI (Google Form / Accounting sheet) vs settled UPI (ICICI bank emails). Three entities: Clinic (OPD+X-Ray+Procedure) · Sanjeevni Medicos (pharmacy) · NK Pathology (lab). Reads ICICI statement emails from Gmail, compares to staff-entered form data, flags mismatches.
- **Function:** `runUpiReconciliation`
- **1 Trigger:** Time-based, last run Jun 29 12:04 PM, 0% error
- **Sheet 1 — "Accounting details"** — `1AnJWDJsAwtgkfFCQNwLzi6lqPPAfGwd-4TUZkuzrZH8`
  - Owner: `drmanojkragarwal@gmail.com` (shared to clinic hub account)
  - Created: July 2024 — long-running operational sheet
  - Staff log daily collections here: Medical Total, UPI, Expenses, Deposits, Cash Balance + Drive links to medicine/implant PDF copies
- **Sheet 2 — "Daily Clinic Reports"** — `1rwxrqAiLh9xBLezZLe7VqBWeCn3FRf_GZqOAEZi-oWc`
  - Owner: `drmka.ortho@gmail.com`
  - Tabs: `Vehicle_Log` (Track360 data, 2 vehicles UP25AE0028 + UP25Q0997) · `Open_Exceptions` (unresolved UPI mismatches — **15 open as of Jun 29**) · `UPI_Reconciliation` (daily OK/LOGGED>SETTLED/SETTLED>LOGGED flags) · `ICICI_[merchant]` ledger tabs · `ICICI_Monthly`
- **Note:** This is a complete daily financial control system — independent of the Callback Tracker. Staff enter collections via Google Form → script compares to bank settlements → flags discrepancies for resolution.

### 2.3 DailyClinicReports ⭐ (starred — active)
- **Purpose:** Email → Google Sheets automation. Reads daily from Gmail (Track360 vehicle reports + ICICI bank statements for 3 merchant accounts). Appends to "Daily Clinic Reports" sheet.
- **Function:** `runDaily`
- **1 Trigger:** Time-based, last run Jun 29 11:39 AM, 0% error
- **Linked Sheet:** "Daily Clinic Reports" — `1rwxrqAiLh9xBLezZLe7VqBWeCn3FRf_GZqOAEZi-oWc`
- **Note:** This script populates the sheet. UPI Reconciliation script reads Accounting details and writes reconciliation results to the same sheet. Two scripts share one output sheet.

### 2.4 Clinic Accounting Reports
- **Purpose:** Reads daily entries from "Accounting details" sheet, generates monthly summaries per department (Medical, OPD, X-Ray, Procedure, Lab) with Cash/UPI breakdown, data quality flags (missing dates, duplicates, errors), and writes to "Monthly Accounting Reports" sheet. Auto-generates each month's report.
- **Function:** `runDailyReport`
- **1 Trigger:** Time-based, last run Jun 29 11:53 AM, 0% error
- **SOURCE — "Accounting details":** `1AnJWDJsAwtgkfFCQNwLzi6lqPPAfGwd-4TUZkuzrZH8` (owned by `drmanojkragarwal@gmail.com`)
- **OUTPUT — "Monthly Accounting Reports - Dr Manoj Clinic":** `13eJo58J7G8n846mGlyv-pHpDILQnCrK-8ZZekyi1Hrg`
  - Tabs: `Monthly_Summary` · `Department_Daily_Detail`
  - May 2026 total net revenue: ₹12,57,275 across 5 departments
  - Data quality checks built in: missing dates, duplicates, formula errors all flagged
- **Note:** This is a full financial reporting system. NOT in GitHub. NOT in the Master KB. Should be documented.

---

## 3. Dormant Projects — Action Needed

| Project | Why dormant | Recommended action |
|---|---|---|
| Untitled project (Jun 16) | 0 triggers, unnamed | Open → check code → rename or delete |
| DailyClinicReports (Jun 7) | Old version, 0 triggers | Confirm superseded by Jun 15 version → delete |
| Untitled project (Jun 7) | 0 triggers, unnamed | Open → check code → rename or delete |
| Daily Clinic Reports (Jun 7) | Old version, 0 triggers | Confirm superseded → delete |

**Caution:** Do not delete without opening and confirming the code is not needed. The Jun 7 versions may have been superseded by the Jun 15 DailyClinicReports and Jun 9 Clinic Accounting Reports.

---

## 4. What Claude Cannot See — Actions Needed From You

| What | Where to find it | Why needed |
|---|---|---|
| What the Jun 16 Untitled project does | Open it → read the code | To decide rename vs delete |
| Whether the 3 Jun 7 dormant projects are safe to delete | Open each → confirm they are superseded | Before deleting anything |

**⚠️ Critical finding:** `Clinic Accounting Reports` uses `openByName('Daily Clinic Reports')` — if that sheet is ever renamed, the script breaks silently. Consider changing to `openById()` in a future session.

**⚠️ Ownership note:** "Accounting details" sheet is owned by `drmanojkragarwal@gmail.com` (personal account), shared to the clinic hub account. If sharing is ever accidentally revoked, UPI Reconciliation breaks. Keep this sharing active.

---

## 5. Google Drive — My Drive Structure

### Root level
| Name | Type | Notes |
|---|---|---|
| UpdraftPlus | Folder | WordPress website backups |
| Attachment Hippo | Folder | Email attachment tool |
| **Dr. Manoj Agarwal \| Practice Hub** | Folder | ✅ Main clinic document hub |
| NK PATHOLOGY 2026 planning | Folder | External collaboration |
| Arrow 360 files and shares | Folder | External partner |
| DailyClinicReports | Apps Script | Sits in root — should be moved to Practice Hub |
| Untitled project | Apps Script | Sits in root — investigate |
| Daily Clinic Reports | Apps Script | Sits in root — old version |
| Untitled spreadsheet | Spreadsheet | Unknown purpose — investigate |
| MKA_Practice_Master_Project_Registry.md | Doc | Old project registry |

### Practice Hub subfolders
| Folder | Purpose | Status |
|---|---|---|
| `01 · Website & SEO` | Website, GMB, SEO | Clinic & Growth project |
| `02 · Digital Marketing` | Marketing materials | Clinic & Growth project |
| `03 · Clinic Operations` | Operational docs | Mixed |
| `04 · Vendors` | Vendor management | Clinic & Growth project |
| `05 · Admin & Finance` | Finance, admin | Mixed |
| `06 · Claude Workspace` | **Automation work** | ✅ Primary home for Claude session output |
| `07 · NotebookLM Sources` | NotebookLM corpus | Future — de-identified data |

### `06 · Claude Workspace` subfolders
| Folder | Purpose | What goes here |
|---|---|---|
| `WABA PROJECT` | WhatsApp work | WABA templates, send layer docs |
| `Session 2026-06-11` | Old session folder | Move to Archives |
| `Generated Documents` | ✅ Claude-generated specs | **Today's spec docs go here** |
| `Strategy & Planning` | Strategy docs | Umbrella Architecture, KB |
| `ROI Models & Analysis` | Financial models | Revenue analysis |
| `Archives` | Old session work | Archive old session folders |

---

## 6. Computers (Drive Sync)

| Device | Status |
|---|---|
| My Computer | ✅ Syncing |
| My Laptop | ✅ Syncing |
| My Laptop (1) | ✅ Syncing |
| OLD FILES | Archived device |

**Confirmed syncing as of 30 Jun 2026:**
- `followup_tracker/data/` → Drive (confirmed live)
- `followup_tracker/outputs/` → Drive (confirmed live)

---

## 7. Key Google Sheets

| Sheet | ID | Purpose | Written by |
|---|---|---|---|
| **Clinic Callback Tracker** | `1USjArkqIdrE9hIqerghms76STatM5XTbSW_a9I3klo0` | **The operational spine.** Tabs: `Agents` (7 staff, all active, user IDs confirmed) · `WA_Inbox` (live — patient messages, images, PDFs) · `Followup_Outcomes` · `Callbacks_Today` · `Patient_Master` · `Followups_Today` · `Followups_Settled` · `Followup_Escalations` · `Call_Feed` · `Daily_Monitor` · `Daily_Report_Log`. Created 19 Jun 2026. 225KB. Last modified 29 Jun 9:24 PM. **⚠️ Note:** some outgoing WA messages stored with bare 10-digit numbers instead of `91XXXXXXXXXX` — cosmetic inconsistency, not a functional issue. | Apps Script (13 triggers) + VPS services (wa-receiver, wa-send relay, push_patient_mirror.py) |
| **Accounting details** | `1AnJWDJsAwtgkfFCQNwLzi6lqPPAfGwd-4TUZkuzrZH8` | Staff daily collection log (Medical Total, UPI, Cash, Expenses, Drive PDF links). Owner: `drmanojkragarwal@gmail.com` | Staff via Google Form |
| **Daily Clinic Reports** | `1rwxrqAiLh9xBLezZLe7VqBWeCn3FRf_GZqOAEZi-oWc` | Vehicle_Log + ICICI ledgers + UPI_Reconciliation + Open_Exceptions. 15 open UPI exceptions as of Jun 29 | DailyClinicReports script + UPI Reconciliation script |
| **Monthly Accounting Reports - Dr Manoj Clinic** | `13eJo58J7G8n846mGlyv-pHpDILQnCrK-8ZZekyi1Hrg` | Auto-generated monthly summaries: Medical/OPD/X-Ray/Procedure/Lab · Cash vs UPI · data quality flags. May 2026 net: ₹12,57,275 | Clinic Accounting Reports script |

---

## 8. Trigger Health Summary (as of 30 Jun 2026)

| Project | Triggers | Last run | Error rate | Health |
|---|---|---|---|---|
| Clinic Callback Tracker | 13 | Jun 29 9:23 PM | 0% | ✅ |
| UPI Reconciliation | 1 | Jun 29 12:04 PM | 0% | ✅ |
| DailyClinicReports ⭐ | 1 | Jun 29 11:39 AM | 0% | ✅ |
| Clinic Accounting Reports | 1 | Jun 29 11:53 AM | 0% | ✅ |
| 4 dormant projects | 0 | — | — | 🔴 Review |

**All active triggers are healthy. 0% error rate across all 16 active triggers.**

---

## 9. Observations and Recommendations

### Immediate
1. **13 triggers on Clinic Callback Tracker** — this is more than expected. The correct set per KB is: `runIntradayDigest` (hourly slots) + `rebuildCallFeed` (21:30) + `runSummaryEmail` + `sendFollowupSummary` + `runMorningReport`. Multiple `runIntradayDigest` triggers may be duplicates from a past `setupTriggers` run. Run `setupTriggers` once to clean up — it removes old ones first. Low urgency since error rate is 0%.

2. **3 Apps Script files sitting in Drive root** — should be moved into Practice Hub for tidiness. Not urgent.

3. **Untitled spreadsheet in root** — unknown. Open and identify before it gets lost.

### Soon
4. Open the 3 dormant Jun 7 projects, confirm they are superseded, then delete to reduce clutter.

5. Open the Jun 16 Untitled project — confirm what it does, rename or delete.

6. Open the **Untitled spreadsheet** in Drive root — identify its purpose before it gets lost.

7. Fix `Clinic Accounting Reports` to use `openById()` instead of `openByName()` — low risk currently but fragile if sheet is ever renamed.

### Undocumented live systems — add to KB
The financial operations stack (Systems 2, 3, 4) is fully functional and running daily but entirely undocumented in the Master KB and not in GitHub:
- UPI reconciliation (Clinic + Sanjeevni + NK Pathology vs ICICI bank)
- Vehicle tracking (Track360, 2 vehicles)
- Monthly accounting reports (₹12,57,275 net May 2026)

These belong documented in the Clinic & Growth project KB. Not urgent but should be done before they are accidentally broken.

---

*Auto-generated by Claude Session 18 · 30 Jun 2026. Update this file whenever new Apps Script projects are created or Drive structure changes.*
