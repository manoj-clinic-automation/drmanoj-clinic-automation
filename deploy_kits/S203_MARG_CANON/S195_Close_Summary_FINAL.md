> ## ⚠ RETIRED — DO NOT ACT ON THIS DOCUMENT
> **Retired on 26-Aug-2026.** Successor: **`KB_History_Archive_v1_49_S202.md`, §S195**
> (md5 `06c6670a8a1155959e4f0961ad58e7c5`).
> The whole S195 narrative was folded into the Archive at the S197 fold, recorded in the manifest as
> a pure append with the prefix proven byte-identical. The canon-debt warning this summary carries
> is spent — the fold happened. For **why** anything is the way it is, read the Archive; never take
> a current fact from it.
> Label added at S203, 26-Aug-2026. **Retained, not deleted (F-23).**

# Session 195 — CLOSE SUMMARY (build session, EOS) · 22–23 Aug 2026

The longest build session to date. What follows is the record; the per-topic detail lives
in the `S195_*` docs already in project knowledge (referenced inline).

## Live pins at close

| system | pin / state |
|---|---|
| `/root/finance/finance_app.py` | **`df75024392e31ae99bb3fde9fab24062`** · smoke **654/654** |
| `/root/portal/portal.py` | `ff08980737c107c3babb78b0c5c169c2` (Club2; portal gate 26/26) |
| `/root/deploy/email_agent.py` | `e535c4f8116abd2fe60b7fda334f33ec` |
| GAS `VPS_Push_UPI` (proj "UPI Reconciliation") | `fac84c5b4a5a14b6345d4cce52c1ad39` v2 |
| GAS Inbox Janitor (`Code.gs`, personal) | v2.3 `3be9bb77f5ec7a9d26e498da438c0a79` |
| GAS `Bank_Statement_Relay` (personal) | live, daily 07:00 |
| GAS `Bank_Statement_Filer` v3 (clinic) | live, daily 07:00 |
| GAS `Clinic_Janitor` (clinic) | pasted; `cjSetup()` done |
| GAS `Renewal_Nag` (personal) | pasted; armed (first fire ~6-Sep) |
| GAS `Neft_Draft` (clinic) | `nd_setup()` done — 1st: draft, 25th: finals to Amir |
| Marg router `margpull/signatures.json` | 5 types · `1b21f3bf582d9f19fb8959a5336b0ba0` |
| Medical PC watcher | LIVE, resident, autostart (see `S195_Medical_Watcher_LIVE_Reference.md`) |

## What went live this session

- **Correction checklist** (self-closing) + Excel/WhatsApp/email/CSV handover for Amir;
  Marg-vs-books at save (A1), honest cash position (A2), cash/UPI misclass w/ direction
  (A3), month check (A4). Floored at `FINANCE_CORRECTION_FROM=2026-08-01`.
- **Darpan's cash/UPI accuracy** on his own portal tile + save response.
- **Email agent** now recovers folded + RFC2047-encoded `Q:` subjects (was silently
  dropping any command >~75 chars).
- **`marg_net_sql()`** — the credit-note sign fixed in all 3 readers (the 18-Aug fault).
- **UPI statement chain filled**: GAS backfill loaded 163 statements (medical 8→56, clinic
  55, lab 50, back to 06-Jun). Verdict: cash/UPI split wrong on **1 day since 1-Aug (₹30,
  06-Aug)** — Darpan is accurate.
- **18-Aug corrected & approved at 25,176**; 20-Aug approved; 21-Aug applied.
- **Bank statement chain** end-to-end: relay (personal) → filer (clinic) → archive + both
  accountants (Hemant Mourya, Shyam Agarwal) + Amir (Sanjeevni, per-attachment 1923/9819).
- **Two inboxes janitored** (personal v2.3 fix + new clinic janitor).
- **Renewal nag** — persistent escalating reminders (replaces easily-swept calendar pings).
- **NEFT monthly automation** — draft on the 1st, finals to Amir on the 25th; Aug draft +
  July finals already placed. Requirements doc `Accounts_Monthly_Requirements_v1_2026-08`.
- **Marg report router**: 5 self-classifying types (sale, closing stock, expiry,
  supplier-wise + bill-wise purchase). `margpull/` mirrored to repo (was a SPOF).
- **Medical-PC resident watcher** — overwrite-proof capture, watches `D:\MARGERP\users` +
  `D:\MARG REPORTS`, autostart via Startup folder, portable Python. Raw mirror of
  `D:\MARG REPORTS` → `margsync\marg_reports_mirror`.
- **Publishers hardened** (stale-git-lock self-clear). **Auditor seeded** (`AUDITOR_SEED_v1`).

## Faults found & fixed (the session's real lessons)

- **Credit-note sign** counted twice in 2 of 3 readers → the 18-Aug "23,879" phantom that
  nearly reversed a correct correction. (`S195_Credit_Note_Sign_Fault.md`)
- **Repeated rollbacks, one root habit:** asserting against shapes not printed — invented
  fixture, guessed JSON, self-matching search string, reserved `$args`, mis-diagnosed
  encoding. Remedy adopted: `pyflakes` + `tools/check_late_locals.py` +
  `tools/check_row_keys.py` before packaging any kit; **never assert against an unprinted
  shape.**
- **8-of-90 blind monitor** — a clean checklist meant no bank data, not agreement. The
  health page's UPI-evidence line is the coverage witness.
- **Medical PC had no system Python** (Store stub) — the whole watcher-install saga.
  Standard adopted: bundled `pyportable`, full-path, never system install (Task #10).
- **manojz cannot write to medical** (read-only share) — every "push to medical" feature
  assumed an OS-forbidden write. (`S195_ToMedical_Pipe_Broken.md`)

## Owner decisions recorded at close (22–23 Aug)

1. **Token rotation → PARKED to next session** (both exposed tokens still live).
2. **17-Aug ₹20,000 → Staff Ledger**: to be done **only against a written application from
   Darpan, scanned** first. Not yet actioned. Drawer stays off ₹175,201 until then.
3. **Medical delivery pipe**: owner will **install Google Drive for Desktop on the medical
   PC** — so ToMedical becomes a mounted-drive local copy, and the medical-side puller
   build is DROPPED. (When installed: wire a simple local copy `Drive:ToMedical →
   D:\SendToClinic\FROM_CLINIC`.)

## Owed / next session (owner-set priorities)

1. **Attendance / salary part** (owner flagged as important — start here).
2. **Portal health tile — renewals line** (Task #8: GAS → VPS → health page).
3. **Start the Auditor in its own background chat** (`AUDITOR_SEED_v1.md`, slice 1 = cash
   trail, calibration run).
4. Carry-overs: token rotation (#1 above); 17-Aug ledger once Darpan's scan exists; medical
   Drive-for-Desktop then the local ToMedical copy; Labmate router sample; `portal.py`
   accuracy-tile render; **canon fold-in debt** (see below).

## ⚠ Canon fold-in debt — for a dedicated EOS-light session, NOT rushed here

The canonical **KB Register / History Archive / CANONICAL_MANIFEST** are folded to **S192**.
Sessions **193, 194, and this 195** exist as standalone `S19x_*` close docs, **not yet
folded** into the Register/Archive/manifest, and `live_pins.txt` is correspondingly stale.
Per D247/F-23 discipline, bolting three sessions of change onto a stale canon at the tail of
an exhausting build session is exactly how a stump/delta fault gets made. **Recommended: a
dedicated fold-in (EOS-light) session** that folds 193→194→195 into Register + Archive,
rebuilds the manifest (A7) and live pins (A8), and writes the Notion logs for any missed
closes. Flagged so it is not lost — this is the honest state, not a skipped step.
