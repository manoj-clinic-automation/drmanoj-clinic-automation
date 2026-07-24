# DOSSIER — Gmail/Drive Automation + Renewals Suite

### Sole reference document. Supersedes KB\_MASTER.md and all interim notes.

|||
|-|-|
|**Product**|Gmail/Drive Automation + Renewals Suite (personal account)|
|**Version**|v2.2.1|
|**Status**|**OPERATIONAL**|
|**Owner**|Dr. Manoj Agarwal — drmanojkragarwal@gmail.com|
|**Frozen**|24-Jul-2026|
|**Canonical copy**|GitHub `drmanoj-clinic-automation/gmail-automation/`|
|**Mirrors**|Notion Tech \& Systems Register row `3a618b9d-8f91-81e1-88a9-e35794da694a` · session cold kit|

\---

## 1\. PURPOSE \& SCOPE

Automates the recurring administrative load of a solo surgical practice's **personal** Google account:

1. **Statement capture** — credit-card statement PDFs land in Drive automatically, named and foldered by card.
2. **Inbox hygiene** — a rules engine files payments, bank alerts, auto-reports, vendor promos and newsletters; trashes only worthless classes (OTPs, content newsletters).
3. **Payment register** — every payment mail becomes a row in a Google Sheet with the receipt saved to Drive, plus a monthly digest.
4. **Renewals** — one system of record for every dated obligation (business, infrastructure, insurance, identity documents, civic, vehicles) driving Google Calendar reminders 30 and 7 days ahead.
5. **Tally handoff** — a PC-side Python pipeline decrypts statements, extracts transactions, and produces the spreadsheet + CSV the accountant works from, launched from the Clinic Hub dashboard.

**Out of scope** (separate systems, separate documentation): clinic Practice Hub on the work account (drmka.ortho), VPS-hosted services (GutLog, follow-up receiver, attendance, WhatsApp stack), track360 vehicle-report processing (its own GAS in the clinic account), ONtime attendance (migrated to the VPS attendance system — its mail is now treated as noise here).

\---

## 2\. ARCHITECTURE

```
GMAIL (personal)
  │
  ├── GAS #1  CC Statement Saver ......... trigger: daily 06–07
  │      └─> Drive /Credit Card Statements/<card>/YYYY-MM-DD\_<subject>.pdf
  │          labels thread: CC-Saved + banks/credit card
  │
  └── GAS #2  Inbox Janitor v2.2 ......... trigger: daily 07–08
         ├─ RULES ENGINE (5 rules: label · save attachments · register · markRead · archive after N days)
         ├─ runSweeps\_()  (trash/archive classes the rules engine doesn't cover)
         ├─ Payment Register sheet  +  monthlyPaymentDigest (1st of month)
         └─ syncRenewalReminders()  \[MANUAL, idempotent]
                └─> GOOGLE CALENDAR
                     ├ RENEWALS\[26]        → all-day events, 30d + 7d email reminders
                     └ ANNUAL\_RENEWALS\[6]  → yearly recurring series, same reminders

DRIVE (personal)                          PC (Windows, D:\\Scripts)
  Credit Card Statements/  ──Drive for Desktop──>  process\_statements.py
  Payment Records/                                    ├─ pikepdf decrypt  → Decrypted/ mirror
  Renewals Master v2 (sheet)                          ├─ pdfplumber + TXN\_RE
  Personal Documents – Renewals (sheet)               ├─ All\_Transactions.xlsx (sheet per card)
  Payment Register (sheet)                            └─ tally\_entries.csv (Suggested Ledger)
                                                             ▲
                                          CLINIC HUB (localhost dashboard)
                                            clinic\_hub.html + open\_clinic\_hub.bat
                                            └─ statements\_app.py :5059 ──┘
                                               auto-runs once daily on hub launch
```

**Design principles** (each one exists because of a specific failure mode):

1. **Sender-username matching, not domain matching** — Indian banks migrated domains in 2026 (hdfcbank.net → hdfcbank.bank.in, icicibank.com → icici.bank.in). Matching `from:(credit\_cards OR emailstatements …)` survives that; domain matching would have silently stopped working.
2. **Dedup by title on calendar sync** — `syncRenewalReminders()` can be run any number of times; it only creates what's missing. Never destructive.
3. **Idempotent sheet updaters** — `applySheetUpdatesOnce()` inspects each row before writing, so re-running cannot duplicate rows or overwrite corrections.
4. **Trash is a narrow privilege** — only OTPs and content newsletters are ever trashed, and Gmail keeps trash 30 days. Everything else is labelled and archived, permanently searchable.
5. **Explicit exceptions beat clever rules** — JustDial is deliberately kept on the archive-only newsletter rule and out of every trash list, because the domain-transfer EPP mail arrives from them (Aug-2026 deadline).
6. **Repo is canonical** — GAS projects are deployed by full-file paste from the repo copy, never edited in place and back-ported.

\---

## 3\. COMPONENT INVENTORY

|#|Component|Runtime|Location|Repo path|
|-|-|-|-|-|
|1|CC Statement Saver|Google Apps Script|GAS project, personal Gmail|`gas/cc-statement-saver/save\_cc\_statements.gs`|
|2|Inbox Janitor v2.2 FINAL (504 lines)|Google Apps Script|GAS project, personal Gmail|`gas/inbox-janitor/inbox\_janitor\_v2.2\_FINAL.gs`|
|3|Narration patch — **NOT deployed**, gated on accountant|Google Apps Script|—|`gas/inbox-janitor/pending/03\_pending\_patch\_friendly\_narrations.gs`|
|4|Statement processor|Python 3.14.5|**D:\\Scripts\\process\_statements.py** (live, with passwords)|`scripts/process\_statements.py` (passwords stripped)|
|5|Statements runner (web UI)|Python / Flask|**D:\\Scripts\\statements\_app.py**, port 5059|`scripts/statements\_app.py`|
|6|Clinic Hub dashboard|static HTML|PC|`clinic-hub/clinic\_hub.html`|
|7|Hub launcher|batch|PC|`clinic-hub/open\_clinic\_hub.bat`|
|8|GMB Review Assist|static HTML|PC|`clinic-hub/GMB\_Review\_Assist\_DrManojAgarwal.html`|

### 3.1 CC Statement Saver

Searches `from:(credit\_cards OR emailstatements OR emailstatements.cc) subject:"credit card statement" after:2025/03/01 -label:cc-saved has:attachment`, derives the card folder from the subject line (**HDFC Business Regalia · ICICI Amazon Pay · ICICI Card 5007 · Other Cards** fallback), saves each PDF with a `YYYY-MM-DD\_` prefix, then labels the thread `CC-Saved` so it is never reprocessed. First run captured **32 statements**.

### 3.2 Inbox Janitor v2.2 — rules engine

Each rule declares: `query · label · saveAttachments · register · markRead · archiveAfterDays`.

|Rule|Matches|Action|Archive after|
|-|-|-|-|
|payments|payment/receipt mail (VENDOR\_MAP: razorpay, anthropic, myoperator, googleplay, apple, samsungcheckout, airtel, cashfree, godaddy, hostinger, sarvam, docterz, gstinvoice, agilus, insurance)|label `PAYMENT RECORDS` + save attachment to `Payment Records/<Vendor>/` + append row to Payment Register|30 d|
|bank alerts|bank transaction alerts|label `banks`|7 d|
|newsletters (archive)|newsletter senders incl. **JustDial**, mapmygenome, maildesq, deepstash, instagram|label + archive|3 d|
|**auto-reports**|ICICI Merchant Solutions MPR, track360, NSDL-CAS, BSE, NSE, ONtime (subject-matched)|label `Reports` + mark read|2 d|
|**vendor promos**|arrow, pepperfry, omron, TTBS, atreya, satvic, Art of Living, dropbox, IASCON, IOACON, citadel, extensionerp, YES marketing, shiprocket, Google Business|label `Vendor-Archive` + mark read|1 d|

### 3.3 Inbox Janitor v2.2 — sweeps (`runSweeps\_()`, runs inside `runJanitor`)

|Sweep|Target|Action|Age|
|-|-|-|-|
|OTPs|subject OTP / one-time password / verification code / login code, **never starred**|**trash**|1 d|
|Content newsletters|SWEEP\_NEWSLETTER\_TRASH list (myclaw, aisecret, medscape, TED, servicespace, beehiiv, IFTTT, rosebud, pocket, deepstash, instagram)|**trash**|1 d|
|MyOperator|`from:myoperator` **excluding** `alert.myoperator.info` (payment path preserved)|label `MyOperator` + archive — **never trashed**, content is occasionally valuable|7 d|
|CC-Saved|statements already filed to Drive|mark read + archive|30 d|

### 3.4 One-shot / manual functions

1. `applySheetUpdatesOnce()` — **idempotent**; applies any missing corrections to both renewal sheets, skips what is already correct.
2. `sweepBacklogOnce()` — clears current backlog with no age limits, batch 100 per category; **repeat until the log prints all zeros**.
3. `syncRenewalReminders()` — creates missing calendar events/series. Run after any renewals edit.
4. `monthlyPaymentDigest()` — monthly summary email (trigger, 1st).
5. `cleanupLabels()` — historical, already executed (\~55 labels removed). Do not re-run casually.

### 3.5 process\_statements.py

`pikepdf` decrypts each PDF using `CARD\_PASSWORDS` → writes a `Decrypted/` mirror → `pdfplumber` + `TXN\_RE` parse transactions → `All\_Transactions.xlsx` (one sheet per card) + `tally\_entries.csv` with a Suggested Ledger column from `LEDGER\_MAP` keywords. Validated run: **32 statements decrypted, 244 transactions**, row counts spot-checked against the ICICI Amazon Pay 13-May–12-Jun-2026 statement (₹2.44 L) ✓.

### 3.6 Clinic Hub + statements runner

`clinic\_hub.html` is a local dashboard of cards with live status dots; `open\_clinic\_hub.bat` starts each service if its port is not already listening.

|Card|Port|Started by|
|-|-|-|
|Case Pack|5058|hub launcher|
|Follow-up Tracker|5000|`open\_tracker.bat` (manual)|
|Vitals|5057|hub launcher|
|**CC Statements → Tally**|**5059**|hub launcher|
|GMB Review Assist|—|static file|

`statements\_app.py` shows last-run time with an OK/FAILED badge, the full output of the last run, and a **Run now** button. On startup it checks the stored last-run timestamp and, if older than **20 hours**, runs the processor in the background after a 5-second delay. All runs — button or automatic — append to `process\_statements.log`. Bound to `127.0.0.1` only.

\---

## 4\. DATA STORES \& CANONICAL IDs

|Store|ID / path|
|-|-|
|**Renewals Master v2** (26 rows)|`1OB70\_Mapuugc33zkfFevwnrS0e8s1NdWzsrzJDqO38E`|
|⚠️ dead ID in older notes — never use|~~`1KMwaBavS3fXSZ7AzHXGcggVAiKuPR0sTfC-wtH58DsM`~~|
|Personal Documents – Renewals (9 rows)|`1NqVH0Eb8625P9\_twFybayA-30Y0z30X-B-4BdBYW8L8`|
|Payment Register|`1wKMcAWMz5VqjoC7q5AgbRvB0xEODrUvibRQw4iRPAHY` (also GAS script property `REGISTER\_ID`)|
|Drive — Credit Card Statements/|`1XpDt8YMovgMBivMC4\_aBvK\_gwTESCAA6`|
|Drive — Payment Records/|`1DOEzqTMGtPqEfgOAeO8dCNWp5KZtOg5x`|
|Notion register row (this product)|page `3a618b9d-8f91-81e1-88a9-e35794da694a`, data source `e2e5e030-efc6-41a3-8f8a-70e808aaa5cb`|
|Gmail labels in use|`PAYMENT RECORDS` · `banks` · `Reports` · `Vendor-Archive` · `MyOperator` · `CC-Saved` · `Janitor-Done`|
|PC paths|`D:\\Scripts\\` (process\_statements.py, statements\_app.py, logs) · Drive for Desktop mount of Credit Card Statements|

**Payment Register columns:** Date | Vendor | Description | Amount (Rs) | Attachment | Gmail link.
**Renewals Master v2 columns:** Category | Item | Vendor/Authority | Holder | Next Due | Cycle | Amount | Notes | Source.

\---

## 5\. SCHEDULES

|Job|Function / entry|Schedule|Status|
|-|-|-|-|
|Statement capture|`saveCcStatements`|daily 06:00–07:00|✅ live|
|Inbox janitor + sweeps|`runJanitor`|daily 07:00–08:00|✅ live|
|Payment digest|`monthlyPaymentDigest`|monthly, 1st|⚠️ believed set — verify on next GAS visit|
|Renewal sync|`syncRenewalReminders`|**manual by design** — run after any renewals edit|idempotent|
|Statement processing|Clinic Hub `:5059`|**auto once daily on hub launch** (>20 h guard) + Run-now button|✅ live|

**Task Scheduler is deliberately NOT used.** Decision (24-Jul-2026): the hub launch is the reliable daily ritual; a fixed-time scheduled task fails silently when the PC is off or asleep, and cannot catch up. The 20-hour guard makes hub launch both the trigger and the catch-up mechanism. If `run\_statements.bat` or a Task Scheduler entry exists from earlier experimentation, **delete them**.

\---

## 6\. CONFIGURATION — WHERE TO EDIT WHAT

|Need|Edit|
|-|-|
|Add a dated renewal|`RENEWALS\[]` entry: `{ vendor, dateISO, cycleMonths, note }` where **dateISO = expiry − lead**. Then run `syncRenewalReminders()`.|
|Add a fixed-anniversary renewal|`ANNUAL\_RENEWALS\[]` entry: `{ title, firstISO, note }` → creates a yearly series.|
|Park a renewal without a date|set `dateISO` to a string starting `TODO` — sync skips it silently.|
|Silence a noisy sender|add to the relevant rule query (`RULE\_REPORTS`, `RULE\_VENDOR\_PROMOS`, newsletters) or `SWEEP\_NEWSLETTER\_TRASH` for trashing.|
|Clear an existing backlog after a config change|`sweepBacklogOnce()`, repeat until zeros.|
|Add a payment vendor|`VENDOR\_MAP` (controls register naming + Drive subfolder).|
|Card password / new card|`CARD\_PASSWORDS` in **D:\\Scripts** copy only — never in the repo.|
|Ledger mapping for Tally|`LEDGER\_MAP` keywords in `process\_statements.py`.|

**Lead times in force:** passports 12 months · arms licence 90 days · driving licences 30 days · vehicle RC 30 days · insurance/infra 30 days.

\---

## 7\. RENEWALS REGISTER (as synced)

**One-off dated entries — RENEWALS\[26]:** 17 business/infrastructure items (domains, VPS, Marg, MyOperator ₹2.12 L Sep-2027, Docterz 5-year to 25-Sep-2027, indemnity ×2, vehicle ×2, health, biomedical waste ×2, fire, CMO to 2030, etc.) plus the personal-document set below.

|Item|Expiry|Action date|Lead|
|-|-|-|-|
|Arms licence — Manoj (LN33013A7C39319/1028/2007, UIN 330130012051232015)|**26-12-2026**|**27-09-2026**|90 d|
|DL — Manoj (UP25 20040006175)|26-12-2027|26-11-2027|30 d|
|DL — Bhawna (UP25 20040001711)|**renewed 2026, date pending**|TODO placeholder|30 d|
|DL — Raghav (UP25 20130009667)|05-06-2033|06-05-2033|30 d|
|DL — Gauri (UP25 20250007671)|16-07-2043|not yet added|30 d|
|Passport — Manoj (T2864619)|15-08-2029|15-08-2028|12 mo|
|Passport — Bhawna (T7363710)|13-08-2029|13-08-2028|12 mo|
|Passport — Gauri (U2373491)|02-01-2030|02-01-2029|12 mo|
|Passport — Raghav (Z7420519)|22-08-2033|22-08-2032|12 mo|
|VW Vento registration (RC)|Jun-2028|01-05-2028|30 d + fitness inspection lead|

**Yearly recurring series — ANNUAL\_RENEWALS\[6]:**

|Series|Anniversary|
|-|-|
|Nagar Nigam annual renewal — Clinic|1 January|
|Nagar Nigam annual renewal — NK Pathology|1 January|
|Nagar Nigam municipal taxes|May|
|Bareilly Club membership|June|
|TVS Star City UP-25-Q-0997 insurance (Bhawna)|5 December|
|Honda Aviator UP-25-AE-0028 insurance (Manoj)|19 January|

Both two-wheeler policies are **current**, renewed offline through an agent on fixed anniversaries; there is no email or Drive trail, which is precisely why they are on calendar series. Last known policies: National Insurance 461300312310001832 (TVS) and 461300312310002129 (Aviator).

\---

## 8\. OPERATIONS RUNBOOK

1. **Monthly accounting cycle** — Saver files statements automatically → open the Clinic Hub (processing runs itself, or press Run now) → collect `All\_Transactions.xlsx` + `tally\_entries.csv` from the Drive folder → hand to Hemant.
2. **Add / change a renewal** — edit `RENEWALS` or `ANNUAL\_RENEWALS` → save → run `syncRenewalReminders()` → confirm the new event appears.
3. **Deploy a new Janitor version** — select all in the GAS editor, delete, paste the repo copy, save. Triggers survive. If the version ships sheet changes, run `applySheetUpdatesOnce()` (safe to repeat).
4. **New noise source appears** — add the sender to the matching rule, save, then `sweepBacklogOnce()` for immediate effect; the daily trigger maintains it thereafter.
5. **Health check** (60 seconds) — GAS *Executions* list shows green for both projects · `sweepBacklogOnce()` printing all zeros means steady state · the hub card badge shows the last processing result · label counts grow, inbox stays small.
6. **Restore a wrongly trashed item** — Gmail Trash, within 30 days.

\---

## 9\. TROUBLESHOOTING

|Symptom|Likely cause|Fix|
|-|-|-|
|Statements stop being saved|bank changed sender username, or subject wording changed|inspect a sample mail, extend the Saver query; the folder mapping is subject-derived|
|A renewal event never appeared|`dateISO` still `TODO`, or the date is in the past (sync skips past dates)|correct the entry, re-run sync|
|Duplicate calendar events|title changed between runs (dedup is by exact title)|delete the stray event; keep titles stable|
|Duplicate sheet rows|a non-idempotent one-shot was run twice|delete the extra rows; only `applySheetUpdatesOnce()` is safe to repeat|
|Hub card dot stays grey|port 5059 not listening — Python or Flask missing, or file not in D:\\Scripts|run `statements\_app.py` manually in a console and read the error|
|Processing produces 0 transactions|statement layout changed → `TXN\_RE` no longer matches|supply one decrypted PDF layout and update the regex|
|PDF fails to decrypt|password missing/changed for that card|update `CARD\_PASSWORDS` locally|
|Payment mail not registered|vendor not in `VENDOR\_MAP`|add it, then `sweepBacklogOnce()`|

\---

## 10\. SECURITY \& SHARING

1. **`CARD\_PASSWORDS` exist only in the D:\\Scripts copy.** The repo copy ships stripped. Never commit filled values.
2. Both Flask services bind to `127.0.0.1` — not reachable from the LAN.
3. Sensitive Drive files audited 23-Jul-2026 and confirmed **owner-only**: STAFF SALARY, Accounting details, Personal Documents – Renewals (contains passport and licence numbers).
4. GAS projects have been renamed from "Untitled project" so Google security alerts are identifiable.
5. **Intended accountant access (Hemant, hemantmourya47@gmail.com, Viewer, from the personal account):** Payment Register sheet · `Payment Records/` · `Credit Card Statements/`. **Verification on 23-Jul showed all three still owner-only — this remains open item #1.** Folder-level sharing means future auto-saved files are visible without re-sharing.
6. Trash-eligible classes are limited to OTPs and content newsletters by deliberate design.

\---

## 11\. OPEN ITEMS

|#|Item|Blocked on|
|-|-|-|
|1|🚩 **Hemant Viewer shares — redo and verify** (3 items in §10.5)|user action|
|2|**Bhawna DL expiry date** → set `dateISO` = expiry − 30 d, update Personal Docs row, re-sync|Parivahan/DigiLocker lookup|
|3|**Narration patch** — paste `pending/03…gs`, run `rebuildRegister()`, update the `.py` narration column (needs 5–6 sample rows)|accountant's verdict|
|4|Verify `monthlyPaymentDigest` trigger exists|next GAS visit|
|5|Drive tidy — 2 × "Untitled spreadsheet", root sprawl (suggest `Clinic Ops/`, `Finance \& Accounts/`, `Reference \& Notes/`), TPA 2022 folder, orphan SHAVEZ shortcut, "FAIZ Consent Form)" typo|optional|
|6|Obtain two-wheeler policy PDFs from agent at next renewal → Drive|Dec-2026 / Jan-2027|

**Known upstream gap (informational):** HDFC Jan and Feb 2026 statements are absent from the mailbox entirely — nothing to capture.

**Live deadlines:** 12-Aug-2026 start drmanojagarwal.in transfer JustDial → Hostinger (EPP mail protected from trash rules) · 29-Aug-2026 dr-manoj.in GoDaddy renewal · 27-Sep-2026 arms licence action · 05-Nov-2026 first TVS insurance reminder fires.

\---

## 12\. RECOVERY

1. **Code** — the repo is canonical; either GAS project can be rebuilt by full-file paste, and the PC scripts by copying back to `D:\\Scripts` (then re-entering card passwords locally).
2. **Calendar** — deleting a wrong event and re-running `syncRenewalReminders()` recreates only intended entries.
3. **Sheets** — Drive version history covers all three; `rebuildRegister()` (pending patch) can rebuild the Payment Register from labelled mail.
4. **Mail** — trash retains 30 days; everything else was archived, never deleted.
5. **Cold start for an assistant session** — hand over the cold kit: this dossier + the latest EOS handoff + all source files.

\---

## 13\. VERSION HISTORY

**v2.2.1 — 24-Jul-2026 — current.** Statements runner integrated into the Clinic Hub (`statements\_app.py`, port 5059, Run-now button, last-run badge, unified log, auto-run once daily on hub launch with a 20-hour guard); hub card + launcher patched; **Task Scheduler approach evaluated and dropped**; dossier consolidated (supersedes KB\_MASTER.md); clinic-hub files added to the repo.

**v2.2 — 23-Jul-2026.** Rules engine gained `markRead`; new auto-reports (2 d) and vendor-promos (1 d) rules; sweeps added (OTP 1 d trash, content newsletters 1 d trash with the JustDial exception, MyOperator 7 d archive-never-trash, CC-Saved 30 d); RENEWALS 17 → 26 (personal documents merged, arms licence confirmed 26-12-2026, Vento RC added, Bhawna DL placeholder); ANNUAL\_RENEWALS\[6] introduced including both two-wheelers; idempotent `applySheetUpdatesOnce()`; Master v2 grown to 26 rows and both sheets verified by direct Drive read; Gmail backlog cleared (35 threads trashed, 32 archived manually, 95 report threads swept); daily triggers set for both projects; Master v2 canonical ID corrected; Notion register row created.

**v2.1 — 22/23-Jul-2026.** Three-rule janitor, Payment Register + monthly digest, 17-entry RENEWALS synced to 17 events, label cleanup (\~55 removed), CC Statement Saver deployed (32 statements captured), `process\_statements.py` validated (244 transactions).

**v1 — Jul-2026.** Initial renewals sheet; superseded and trashed.

