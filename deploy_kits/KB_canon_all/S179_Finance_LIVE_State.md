# SANJEEVNI FINANCE MODULE — LIVE STATE

**Session 179 · 15 Aug 2026 · installed and running on the VPS**
Contract: `S179_Clinic_Finance_System_Build_Contract_v2` · analysis:
`S179_Finance_Revenue_Migration_Analysis_v1` · B1 output: `S179_B1_Medical_Reconciliation_Report`

---

## 1 · What is live

| | |
|---|---|
| URL | `https://followup.dr-manoj.in/finance/` — routes by role |
| Home | `/root/finance/` · service `clinic-finance.service` · gunicorn on `127.0.0.1:8106` |
| Vhost | `followup.dr-manoj.in` — `context /finance` → `extprocessor finance_app` |
| Auth | `clinic_sso` cookie via `/root/portal/clinic_sso.py`; roles from `unit_role`, by name |
| Data | `finance.db` — 121 imported days, Apr 1 → Aug 13 2026, ties to the sheet exactly |
| Backups | `/root/backups/finance/` — nightly 01:05, 30 daily + 12 monthly, each verified before pruning |
| Portal | tiles **Daily Sale** (staff → `/finance/entry`) and **Sanjeevni Medicos** (doctor → `/finance/review`) |

**Live file md5s** (final S179 close — after the day-browse and the UPI installs)

```
61e36d5522e4e99e1e65e159ef50c85e  finance_app.py
872ec33ef7c628cd474224b0c6c78ba5  finance_ingest.py
7cfde93e1c18a030a031a60ff66795f6  finance_import_medical.py
3f5016f0c64f12b91ab55c18252705c1  finance_upi.py
bef0d8100a1d7da30d049a9cd8eaf365  finance_schema.sql
8ec6ad494fd6b97e5c7c70b6c42fdfc5  finance_ui/finance_entry.html
ddd3d5f61fb2f41950b1a63aa3480650  finance_ui/finance_review.html
efe6f1b527bffafc21062bc352a063ee  finance_backup.sh
59c03bfafc2cd63bc440053724b61c34  clinic-finance.service
955b291c99edd0f16c79836e54a1043d  VPS_Push_UPI.gs  (clinic-Gmail GAS, not on the VPS)
```

Gates at final install: app smoke **176/176** · ingest **30/30** · importer **12/12** · UPI parser
**14/14** · all smoke gates proven to leave `finance.db` byte-identical. `healthz` reports
`sso_epoch_ok:true`.

**UPI reconciliation is LIVE (B5).** `finance_upi.py` parses the ICICI Merchant (MPR) `.xlsx`,
self-checks each file against its own Grand Total (rejects on mismatch — `StatementRejected`), and
stores settled UPI per unit per day. `VPS_Push_UPI.gs` in the clinic Gmail pushes the daily MPR to
`/finance/api/upi-statement` (token `X-Finance-Cron`) at 09:30; verified end to end
(`{"ok":true,"pushed":8}`; MID `…312505` = Sanjeevni, `…306941` = clinic, `…319164` = NK Pathology).
Bank is the arbiter: any day whose entered UPI disagrees with the statement flags and **shouts until
acknowledged** — approval requires `acknowledge_upi` over an open mismatch.

**Portal tiles:** `Daily Sale` (staff → `/finance/entry`), `Sanjeevni Medicos` (doctor →
`/finance/review`). Masked: `Sanjeevni Medicos` from `bhawna`; `Attendance` / `Staff Register` /
`Scan Purchase` from `darpan` (role `staff` is shared, so each staff member is shaped by mask).
Logins live in the portal's own user admin — `darpan` added as `staff`.

**Roles in force** — medical: maker `darpan`, checker `manoj`. Clinic and lab seeded with
`reception` / `labstaff` as makers and `manoj` + `bhawna` as checkers, unused until those modules
are built. A broker role grants nothing by itself, not even `doctor`.

---

## 2 · THREE security faults found and fixed after first install (candidate F-84)

All three were mine. All three had the same shape: **something that made development or testing
easier, carried into production without asking "what does this let a stranger do?"**

1. **Reads were ungated.** Identity was checked only on writes, so `/finance/api/tile`,
   `/month`, `/day` and later patient lines were readable by anyone with the URL. Exposure window
   was about two minutes on an unpublicised path.
2. **Identity came from HTTP headers.** `X-Clinic-User` / `X-Clinic-Role` were meant as an offline
   testing convenience and reached production. `curl -H "X-Clinic-Role: checker"` would have
   approved days and run the cutover. That is not a leak, it is control.

**Fixed by:** the real `clinic_sso` cookie; header auth off unless `FINANCE_ALLOW_HEADER_AUTH=1`
(the systemd unit says in plain words why it must never be set); and a **fail-closed
`before_request` gate** on an allow-list, so a route added later is protected without anyone
remembering. Later tightened again: *signed in ≠ entitled* — a valid clinic login with no
`unit_role` row on `medical` gets 403, so Shavez cannot read the pharmacy's cash.

3. **The epoch was never checked.** `verify_token` was called with `current_epoch=None`, so
   **"Sign out everywhere" revoked sessions in the portal, ledger and asset app but not here** — a
   revoked token still opened the books. Found only because a stale epoch caused a 403 on
   `/portal/users` and the diagnosis exposed the asymmetry.

**Fixed by:** reading the epoch from `clinic_users.get_epoch(clinic_users.DEFAULT_STORE)` on every
request (never cached — a cached epoch keeps revoked sessions alive for the life of the cache), and
**failing closed** if it cannot be read, exactly as the portal does. `healthz` exposes
`sso_epoch_ok` so a lockout is diagnosable without a cookie, and the installer rolls back
automatically if that flag is false.

**The lesson worth keeping:** the offline testing shortcut was the vulnerability. Anything that
grants identity for convenience must be opt-in, and the production default must be closed.

**A fourth, smaller lesson:** one install was rolled back by its own gate because a *test* asserted
an environment accident ("the epoch is unreadable here") rather than a behaviour. Tests should
assert what the code does, not what the machine happens to look like. The replacement forces the
epoch to be unreadable and requires refusal — deterministic on any box.

---

## 3 · What the data says (from B1)

- **121 days imported as recorded**; the ledger reproduces the sheet's own closing to the rupee
  (−₹30,056), which is what proves the import faithful.
- **36 carry-forward breaks**, net **−₹84,533** — each now an open, dated, sized row awaiting a
  reason, not a number lost in a column.
- **7 days of negative cash in hand**, physically impossible, all imported honestly rather than
  smoothed.
- **14 missing days** at import; the system began asking for 14 Aug on its own the next morning.

**Two findings that change what the drift means:**

- **1 Aug's opening was typed as ₹0** against a 31 July closing of ₹38,176. April→May and May→June
  carried correctly, so this is a keystroke, not a monthly policy. The largest August break is a
  habit, not missing money.
- **31 July's closing is not a clean anchor.** It rests on a **+₹45,000** correction typed that
  morning, after an **₹85,000 deposit on 30 July** drove the drawer to −₹16,485 against about
  ₹68,500 held. One look at the bank statement for 30 July likely resolves the largest July break.

---

## 4 · Design decisions worth carrying forward

- **Opening cash is computed and has no input anywhere.** The 36 breaks are structurally impossible
  to repeat.
- **Revenue counts in full; cash does not.** Home and procedure medicines are billed whole with no
  cash across the counter — recorded as `day_noncash_bill`, reducing the drawer, never the revenue.
- **The drawer carries.** Cash reaches the bank on a trip days later, so month close records what
  carried rather than demanding a sweep. Banking is driven by the ₹50,000 threshold and a
  days-since-trip counter.
- **A deposit is never split.** One movement, one slip, one date, matching the bank. Only the *old*
  month's share is named (`clears_ym` / `clears_amount_p`); the remainder is this month's by
  definition. Cash parked past 21 days shouts.
- **A missing day is never silenced** — not for Sunday, not for absence. It stays pinned until filed.
- **Attribution never moves the books.** Patient-wise lines reconcile against the day total; they
  cannot change it.
- **The line source is an adapter**, not an assumption: `sarvam_ocr` today, `marg_export` /
  `labmate_export` when the real files arrive. Switching is a column map, not a rewrite.
- **Scans are evidence, relocated not deleted.** Month finalisation queues them to Google Drive; the
  attachment row and Drive file id are kept forever.

---

## 5 · Still open

**Owner decisions**

1. **The 30 July deposit** — was it ₹85,000? This gates whether 31 July's closing can anchor the
   August re-entry.
2. **Opening balance / cutover** — owner plans to re-enter August with July's corrected close.
   `Count the drawer` on the review screen does this; running it twice is safe by design.
3. **Off-box backup.** Copies are on the same disk — good against a bad deploy, useless against
   losing the VPS. The file holds patient names, so where it goes is the owner's call.
4. **Accountant packs** — patient names included or revenue lines only (toggle
   `export.include_patient_names`, default off).

**Not yet built**

- B4b Drive archive mover (queue fills meanwhile — the safe failure)
- B6 salary advance → Staff Ledger posting (marked `PENDING_LEDGER_WIRING` on approval)
- B7 month export `.xlsx` / `.pdf`, per entity
- Missing-day WhatsApp nudge cron (`/finance/api/shout` exists)
- **Marg adapter** — the sale-report `.xls` beats Sarvam decisively (13/13 exact day matches; see
  `S179_Marg_Sale_Report_Analysis`); needs its own adapter (date lives in group-header rows; real
  BIFF `.xls`; day-total self-check). Cash = the CASH column, UPI = net − CASH (never the mode field).
- Labmate column map — awaiting one real export
- Clinic and lab modules

**DONE this session (was open earlier):** B5 ICICI UPI ingester — now LIVE (see §1). All three
merchant IDs confirmed, incl. NK Pathology `…319164`.

**Also live (added after the first record):** every day stays openable as a collapsed expandable
line regardless of status; scans are inline links (imported days link to the ORIGINAL Drive file,
because copies were never held — dashed border marks those); Portal back links on both pages and a
Back control on the scan page; parked-cash allocation; Count-the-drawer control.

**Owed before any commit:** `.gitignore` the PHI paths (`finance.db*`, `scans/`, `exports/`,
`vendor/`, `backup.log`, `medical_*.csv`) **before** the first push, not after.

---

---

## 6 · Canonical status

This document is the **sole live-state reference** for the clinic-finance subsystem (Tier 1, opened
on demand). Companions, all in project knowledge: build contract `S179_Clinic_Finance_System_Build_
Contract_v2`, migration analysis `S179_Finance_Revenue_Migration_Analysis_v1`, B1 reconciliation
`S179_B1_Medical_Reconciliation_Report`, Marg feed analysis `S179_Marg_Sale_Report_Analysis`, Marg
folder recon `S180_Marg_Folder_Recon`, and the delivery notes `S179_B1b_B2` / `B2.1` / `B2.2` /
`B3a`. Decision **D313** (finance subsystem architecture) and finding **F-84** (the three security
faults + the offline-testing-shortcut lesson) are minted this session; full text in Archive §S179.

*S179 · live-state record, refreshed at the S179 close to the final live md5s (UPI + browse folded).
Next free: D314 · F-85.*
