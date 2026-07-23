# KB MASTER — Gmail/Drive Automation + Renewals Suite
**System of record. Canonical copy: GitHub `drmanoj-clinic-automation/gmail-automation/`. Mirrors: Notion Tech & Systems Register row · session cold-kit zip.**
Version 2.2 · Status OPERATIONAL · Frozen 23-Jul-2026 (late night IST)

---

## 1. PURPOSE & SCOPE
Personal-account automation suite for Dr. Manoj Agarwal (drmanojkragarwal@gmail.com) covering: (a) automatic credit-card statement capture Gmail→Drive, (b) inbox hygiene via a rules engine (payments, bank alerts, newsletters, auto-reports, vendor promos, OTPs), (c) a Payment Register Google Sheet fed automatically from payment mail, (d) a complete renewals reminder system (business, infra, personal identity documents, civic, vehicles) driving Google Calendar events with 30-day + 7-day email reminders, and (e) a PC-side Python pipeline that decrypts statement PDFs and extracts transactions for Tally handoff to the accountant (Hemant).

Out of scope: clinic Practice Hub (work account drmka.ortho), VPS services (GutLog etc. — separate KB entries), track360 processing (separate GAS in clinic account), ONtime attendance (migrated to VPS system).

## 2. ARCHITECTURE OVERVIEW
```
Gmail (personal) ──┬─ GAS #1 CC Statement Saver (daily 6–7am)
                   │      └→ Drive /Credit Card Statements/<card>/YYYY-MM-DD_*.pdf
                   └─ GAS #2 Inbox Janitor v2.2 (daily 7–8am)
                          ├→ 5 rules engine (label / register / archive / markRead)
                          ├→ sweeps (trash OTPs & newsletters, archive MyOperator, CC-Saved)
                          ├→ Payment Register sheet (auto rows + monthly digest, 1st)
                          └→ syncRenewalReminders(): RENEWALS[26] + ANNUAL_RENEWALS[6]
                                 └→ Google Calendar (all-day events + yearly series,
                                    30d & 7d email reminders, dedup by title)
Drive for Desktop (PC) → D:\Scripts\process_statements.py
                          └→ Decrypted/ mirror · All_Transactions.xlsx · tally_entries.csv
Sheets: Renewals Master v2 (26 rows) · Personal Documents – Renewals (9 rows)
```
Design principles: sender-USERNAME matching (survives bank domain migrations, e.g. icicibank.com→icici.bank.in); dedup-by-title calendar sync (idempotent); idempotent sheet updaters; only OTPs and content newsletters are ever trashed (30-day recovery), everything else archived under labels.

## 3. COMPONENTS
| # | Component | Where | File in repo |
|---|---|---|---|
| 1 | CC Statement Saver | GAS project, personal Gmail | `gas/cc-statement-saver/save_cc_statements.gs` |
| 2 | Inbox Janitor v2.2 | GAS project, personal Gmail | `gas/inbox-janitor/inbox_janitor_v2.2_FINAL.gs` |
| 3 | Narration patch (PENDING, gated on Hemant) | not pasted | `gas/inbox-janitor/pending/03_pending_patch_friendly_narrations.gs` |
| 4 | Statement processor | PC, D:\Scripts | `pc-scripts/process_statements.py` |
| 5 | Session handoff | docs | `docs/EOS_23Jul2026_session3_handoff.md` |

**Janitor v2.2 internals:** rules engine with per-rule `label / saveAttachments / register / markRead / archiveAfterDays`; RULES = payments (30d) · bank alerts (7d) · newsletters-archive (3d) · auto-reports (2d) · vendor-promos (1d). `runSweeps_()` runs inside `runJanitor`. One-shots: `applySheetUpdatesOnce()` (idempotent), `sweepBacklogOnce()` (repeat till zeros), `cleanupLabels()` (historical, executed). `syncRenewalReminders()` = one-off events from RENEWALS + yearly series from ANNUAL_RENEWALS.

## 4. DATA STORES & CANONICAL IDS
| Store | ID / Path |
|---|---|
| **Renewals Master v2** (26 rows) | `1OB70_Mapuugc33zkfFevwnrS0e8s1NdWzsrzJDqO38E` ⚠️ older docs cite dead ID `1KMwaBav…` — never use |
| Personal Documents – Renewals (9 rows) | `1NqVH0Eb8625P9_twFybayA-30Y0z30X-B-4BdBYW8L8` |
| Payment Register | `1wKMcAWMz5VqjoC7q5AgbRvB0xEODrUvibRQw4iRPAHY` (also in Janitor script property `REGISTER_ID`) |
| Drive: Credit Card Statements/ | `1XpDt8YMovgMBivMC4_aBvK_gwTESCAA6` (card subfolders: HDFC Business Regalia · ICICI Amazon Pay · ICICI Card 5007 · Other Cards) |
| Drive: Payment Records/ | `1DOEzqTMGtPqEfgOAeO8dCNWp5KZtOg5x` (vendor subfolders) |
| Gmail labels | PAYMENT RECORDS · banks · Reports · Vendor-Archive · MyOperator · CC-Saved · Janitor-Done |
| PC input | Drive for Desktop path of "Credit Card Statements" (INPUT_DIR in .py) |

## 5. SCHEDULES & TRIGGERS
| Trigger | Function | Schedule | Set |
|---|---|---|---|
| CC Saver | `saveCcStatements` | daily 6–7am | ✅ 23-Jul-2026 |
| Janitor | `runJanitor` (incl. sweeps) | daily 7–8am | ✅ 23-Jul-2026 |
| Digest | `monthlyPaymentDigest` | monthly, 1st | ✅ per user; verify on next GAS visit |
| Renewal sync | `syncRenewalReminders` | MANUAL by design — run after any RENEWALS/ANNUAL edit (idempotent) | — |

## 6. CONFIGURATION REFERENCE (edit points in Janitor)
- **RENEWALS[26]**: one-off action-dated entries. dateISO = expiry − lead. Leads: passports 12 mo · arms licence 90 d · DLs/vehicle 30 d. `TODO`-prefixed dateISO = skipped by sync (current: Bhawna DL).
- **ANNUAL_RENEWALS[6]**: yearly series — Nagar Nigam ×2 (01-Jan) · municipal taxes (01-May) · Bareilly Club (01-Jun) · TVS Star City insurance (05-Dec) · Honda Aviator insurance (19-Jan).
- **Rule sender lists**: extend inside each RULE's query. JustDial is DELIBERATELY archive-only (never in trash list) — protects the domain-transfer EPP mail (Aug-2026).
- **SWEEP_NEWSLETTER_TRASH**: content newsletters trashed @1d.
- **VENDOR_MAP**: payment-mail vendor → register naming / Drive folder.
- **process_statements.py**: CARD_PASSWORDS (local only, never committed) · LEDGER_MAP keywords · TXN_RE.

## 7. OPERATIONS RUNBOOK
- **Add a renewal**: append RENEWALS entry (or ANNUAL for fixed-anniversary) → run `syncRenewalReminders()` → confirm event.
- **Fill Bhawna DL date**: set dateISO = expiry−30d in her entry → update Personal Docs row 2 (expiry/action) → sync.
- **New vendor/promo/report/newsletter sender**: add to the matching rule query or trash list. Daily trigger handles the rest; run `sweepBacklogOnce()` for immediate backlog.
- **Monthly statement cycle**: Saver files PDFs → run process_statements.py on PC → All_Transactions.xlsx + tally_entries.csv → Hemant.
- **Deploy a new Janitor version**: full-file replacement (select-all-paste), save; triggers persist. Run `applySheetUpdatesOnce()` if sheet changes shipped (idempotent, safe).
- **Verify health**: GAS execution logs; Gmail label counts; `sweepBacklogOnce()` log all-zeros = steady state.

## 8. RECOVERY & ROLLBACK
- Canonical code = this repo folder; any GAS project can be rebuilt by full-paste from repo.
- Trash = 30-day recovery for the only trashed classes (OTPs, content newsletters, executed by design).
- Calendar: sync is additive+dedup — deleting a wrong event and re-running sync recreates only intended ones; stale events are deleted manually (done for 3 in v1 era).
- Sheets: Drive version history covers Master v2 / Personal Docs / Payment Register. `rebuildRegister()` (pending patch) can rebuild register from labelled mail.
- Known mailbox gap: HDFC Jan+Feb 2026 statements absent at source (informational).

## 9. SECURITY & SHARING
- CARD_PASSWORDS live ONLY in the local .py on PC — the repo copy ships with an empty/placeholder dict. Never commit filled passwords.
- Sensitive sheets/files verified owner-only (23-Jul audit): STAFF SALARY, Accounting details, Personal Documents – Renewals.
- **Intended sharing (Hemant, Viewer, from personal account): Payment Register + Payment Records/ + Credit Card Statements/. ⚠️ As of 23-Jul verification: NOT in effect (all owner-only) — redo and re-verify. This is Open Item #1.**
- GAS projects renamed (identifiable in Google security alerts) ✓.

## 10. KNOWN ISSUES & OPEN ITEMS
1. 🚩 **Hemant shares** — redo the 3 Viewer shares + verify (see §9).
2. **Bhawna DL expiry date** — renewed 2026, date pending; TODO placeholder self-documents the fix.
3. **Hemant narration loop** — pending his verdict: paste `pending/03…gs` → `rebuildRegister()` → update .py narration column (needs 5–6 sample rows) → redeliver.
4. Verify `monthlyPaymentDigest` trigger exists on next GAS visit.
5. Optional Drive tidy: 2× Untitled spreadsheets · root sprawl (suggested Clinic Ops / Finance & Accounts / Reference & Notes) · TPA 2022 folder · SHAVEZ shortcut · "FAIZ Consent Form)" typo.
6. Next renewal cycle: obtain two-wheeler policy PDFs from agent → Drive (currently no digital trail).

## 11. VERSION HISTORY
- **v2.2 (23-Jul-2026) — OPERATIONAL.** Rules engine +markRead; auto-reports (2d) + vendor-promos (1d) rules; sweeps (OTP 1d trash, newsletters 1d trash w/ JustDial exception, MyOperator 7d archive-never-trash, CC-Saved 30d); RENEWALS 17→26 (personal docs, arms licence confirmed 26-12-2026/action 27-Sep-2026, Vento RC, Bhawna DL TODO); ANNUAL_RENEWALS[6] yearly series incl. two-wheelers; idempotent sheet updater; both sheets Drive-verified; Gmail backlog cleared (95 reports + newsletters + vendors + Arrow archive); triggers set; Master v2 ID corrected.
- v2.1 (22/23-Jul-2026): 3-rule janitor, Payment Register, 17-entry RENEWALS, label cleanup (~55), 17 events synced.
- v1 (Jul-2026): initial renewals sheet (superseded, trashed).
