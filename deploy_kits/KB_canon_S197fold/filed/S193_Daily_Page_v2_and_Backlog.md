# S193 — Daily Sale page v2 (approved design) + live contract + backlog

## Status of the session's finance work (all LIVE unless noted)
Live hashes to pin (KB Register, D321(d)):
- finance_app.py `51245f8ba598fd5603b88fa90b0ca945` (discount + stale-flag). **S193_CASHPOS raises it again — pin what that installer prints.**
- marg_report.py `6411a57d4517e0a06a02e1045b354138`
- finance_ingest.py `a4e9663f9be1c138293d6dd8311577d0`
- finance_approvals.html `2e3b40cc5fc51ad54de2382548a6cdf5` → **S193_CASHPOS supersedes (pin its printout)**

Kits delivered this session (in deploy_kits/): S193_DISC (discount, LIVE), S193_STALE (LIVE),
S193_CUST (LIVE), **S193_CUST2 (SKIP — folded into CASHPOS)**, **S193_CASHPOS (pending owner install;
adds /finance/api/cash-position + Cash position Hub card + custody comma-parse fix)**.

## Cash model (locked)
- Drawer (Darpan) = `v_cash_ledger.closing_p` − reserve − with_manoj. Day-wise + total. Now ₹65,697.
- Reserve (Dr Bhawna) = custody held `dr_bhawna` = ₹1,56,235 (only in cash_custody_event, NOT cash_movement).
- With Dr Manoj = custody held = ₹18,963.
- Bank deposited = Σ cash_movement(party='bank',direction='out') = ₹15,70,600 (15).
- Reconciles: drawer + reserve + manoj = unbanked (₹2,40,895). The old "₹33k float" = Darpan's
  uncounted drawer cash (owner confirmed he has the 17th cash) — no mystery.
- Hand-overs to Bhawna/Manoj are NOT yet recorded as cash_movements ("we will start this soon");
  once they are, reserve tracks live from cash_movement.

## Daily Sale page v2 — APPROVED prototype flow (owner said OK)
Prototype delivered: daily_sale_v2_prototype.html. Build the real page from it.
Flow: Google-form, two stages.
1. **Stage 1 (enter+save):** date · total/UPI (cash auto) · expenses · **3 scans with ✓-uploaded
   confirmation** (or skip-with-reason). Big **① Save** primary; **② Submit** locked until saved.
   Save→loud "Saved". Submit-before-save→loud "Save first". Any edit after save→must re-save.
2. **On Submit:** confirmation "DATE — submitted · Total … · UPI … · Scans 1,2,3 ✓", then reveal
   **Stage 2:** cash + Marg summary, **Transfer-out block** (Bank/Dr Bhawna/Dr Manoj), **live drawer
   post-transfer**, then **Final submit — close the day**.
3. **Transfer-only** path (top button): record a hand-over WITHOUT filing a day.

## LIVE contract (finance_entry.html, reverse-engineered from the served page)
- Save/submit: `POST /finance/api/day` body from collect():
  `{business_date, total, upi, expenses:[{amount,category,uid,details}],
    movements:[{amount,party,direction,reference}]  // TRANSFERS (party bank/dr_bhawna/dr_manoj, dir out/in),
    noncash_bills:[{amount,head,bill_no,bill_date,head_text}], action:'draft'|'submit',
    manned_by, manned_source, attached_docs:[uids], missing_scan_reason}`
- Scans/bills upload: `POST /finance/api/day/<date>/expense-scan/<uid>` (uploadPendingBills).
- Read day: `GET /finance/api/day/<iso>`; also /mirror, /where-is-the-cash, /whoami, /exceptions.
- Drawer figures: `GET /finance/api/cash-position` (built this session).
- Submit-with-pending-bills pattern: draft-save → upload bills → real submit.
- Transfers ride in `movements`. Post-submit transfer = re-POST /day (creates a revision).
  Transfer-only = decide: minimal /day update with just movements, or a small dedicated endpoint.

## Build plan (SAFE)
New page served at a **new route** (e.g. /finance/daily) so the current /finance/entry stays as
fallback. Reuse the proven collect/save/scan JS; restructure UI/flow per the prototype; wire
transfers via movements + cash-position for the drawer. Offline-verify, deliver kit, live-test,
then switch over when owner approves.

## Backlog (queued, in order)
1. **Daily page v2** build (this doc). NEXT.
2. **Home-medicine bills:** populate from Marg export (my call — no manual scan burden); optional
   scan skippable-with-reason. NEED: how a home-medicine bill is marked in Marg (mode/tag/series?).
3. **Cash/UPI reclassification tracker:** on re-import, capture per-bill mode flips (both
   directions) into a new `mode_change_log` (snapshot before the delete-reinsert in
   finance_ingest.ingest_day), show expandable "N bills reclassified" on Hub + Darpan feedback +
   history. Automatic. Amir's conversions stop being silent.
4. **Full-auto ping-pong email query** (needs owner Gmail app password).
5. Housekeeping: stray tarballs under deploy_kits/_to_delete on the box repo (harmless); delete
   root _to_delete from Windows.
