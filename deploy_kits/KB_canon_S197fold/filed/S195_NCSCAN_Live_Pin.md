# S195_NCSCAN — LIVE (21 Aug 2026, 12:16)

Daily Sale v2: no-payment bills restored + per-bill scan, compact mobile layout,
prominent live drawer, loud confirmations, submit-with-attachments list.

## LIVE PINS (update the Register)
- **`finance_app.py` = `f25ed48923a5647ba1f6111bad0737d3`**
  (chain: S194E `d2863c30` → S195_ENTRY `85df28fe` → S195_NCSCAN `f25ed489`)
- **`finance_ui/finance_daily.html` = `20efc5caa664c9b96be23bb66866d21c`**
- Smoke **573/573** before and after · backup `/root/finance/_backup_S195_NCSCAN_20260821_121621`
- Path reminder: the finance app lives at **`/root/finance/`** (NOT /root/deploy).

## What changed
**Page (`finance_daily.html`)** — Day+Sale merged into one compact card (mobile-first);
sticky **drawer strip** showing Darpan's live counter cash (`/finance/api/cash-position`),
refreshed on load/save/hand-over/close; **No-payment bills** section restored (it existed
in v1 `finance_entry.html` and was dropped in the v2 rewrite) with Bill date · Head
(home_medicine / procedure_medicine / other) · Bill number · Amount · Note, a "What for"
box for Other, and a live **Cash actually received**; each bill has its own **📎 Scan bill**
with a loud **✓ Scan saved** badge; Save turns into **✓ Saved**; the Submit screen lists
**every attachment**; Transfer-only moved to the bottom; "Other" party added (backend
already accepted it).

**Backend (`finance_app.py`)** — mirrors the proven expense-scan subsystem:
- `day_noncash_bill` gains nullable **`noncash_uid`**; new table **`noncash_attachment`**
  keyed on (day_entry_id, noncash_uid) so a scan survives the save's delete-and-reinsert.
  Both created lazily (additive DDL, the D330 pattern).
- `POST /finance/api/day` captures a stable uid per bill and stores it.
- Day-read returns each bill's `uid` + `has_file` (drives the ✓).
- New `POST /finance/api/day/<d>/noncash-scan/<uid>` (upload) and
  `GET /finance/scan-noncash/<d>/<uid>` (shared scanner host page).

Note: the no-payment **entry** was always backend-ready (`day_noncash_bill`, validation,
read-back existed since before S194) — the v2 page just hardcoded `noncash_bills:[]`.
Only the per-bill **scan** was new code.

## Deploy history note (why the first attempt stopped)
The first S195_NCSCAN build gated on `d2863c30` (pre-ENTRY). By then S195_ENTRY had made
the live app `85df28fe`, so the installer **refused at step 2 and touched nothing** — the
gate working as designed. The kit was rebuilt on top of the deployed `85df28fe` source,
carrying the `/finance/entry` redirect forward (both changes verified coexisting).

## Still open
- **Email agent did not answer** a `Q: sql …` test on 21 Aug (~06:13 UTC): no reply, no
  `clinic-agent-done` label after two poll cycles. Check `systemctl list-timers | grep
  email-agent`; re-enable with `systemctl enable --now email-agent.timer`. Unrelated to
  this deploy.
- Canon fold (Register/manifest/Archive) still owed from S193/S194/S195.
