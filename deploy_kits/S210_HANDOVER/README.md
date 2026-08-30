# S210_HANDOVER — Darpan records the transfer, including the RETURN leg

## The gap (owner, 30-Aug): "i dont see a money transfer section in his page"

The money model: sale cash reaches Darpan; three routes out — bank deposit, Dr Bhawna,
Dr Manoj — and the doctors mostly hand it BACK for banking later. Until now Darpan's page
could record none of these; the return leg had no entry path anywhere in the system. The
unrecorded return leg is what let a month of takings pile up invisibly (₹3,20,340).

## The two pieces

**1 · `patch_darpan_app_handover.py`** — `POST /finance/darpan/api/handover` (maker or
checker): five kinds — `bank`, `to_bhawna`, `to_manoj`, **`back_bhawna`, `back_manoj`** —
one `cash_movement` row each (the S194 convention), anchored to the latest filed day, with
audit. **The one-record rule is ENFORCED**: a handover already present as a custody event
(same date+party+amount) is refused with a plain-Hindi message — recording it twice would
double-count (the S210 boundary finding, measured to the rupee).
**Selftest 13/13** on BOTH live darpan_app candidates (S208_CONSOLE `b924626f…`,
S208_LEDGER3 `8b1e0653…`).

**2 · `darpan_card.html`** — a "🔁 Cash bhejna / wapas lena" section above the evening
count: pick the route, type the amount, confirm, done. Base: the S210_DRAWERCARD page
(this file supersedes that kit's copy — installing this one is enough for both features).
js_gate PASS.

## Proof — F-87 rehearsal on the seeded store, 10/10 (`REHEARSAL_handover.py`)

Bank deposit: drawer −50,000 AND unbanked −50,000 (it left). To a doctor: drawer falls,
doctor rises, unbanked unchanged. **Return leg: doctor falls, drawer rises, unbanked
unchanged.** Duplicate of an existing custody event: refused, nothing changed. The
invariant drawer+Bhawna+Manoj = unbanked held through every step.

## Install — VPS, one line at a time (server patch ⇒ restart needed)

```
git -C /root/deploy/repo fetch --depth 1 origin main && git -C /root/deploy/repo reset --hard origin/main
```
```
/root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S210_HANDOVER/patch_darpan_app_handover.py /root/finance/darpan_app.py
```
```
\cp /root/finance/darpan_card.html /root/finance/darpan_card.html.bak_S210_HO_$(date +%Y%m%d_%H%M%S)
```
```
\cp /root/deploy/repo/deploy_kits/S210_HANDOVER/darpan_card.html /root/finance/darpan_card.html
```
```
systemctl restart clinic-finance.service && sleep 3 && systemctl is-active clinic-finance.service
```

Walk: open Darpan's page — the new section sits between "Drawer mein hona chahiye" and the
evening count. Record one real handover and watch the owner console's money card move with
it, live, on the same arithmetic.

*S210 · 30-Aug-2026 · built unattended on the owner's standing instruction; nothing
installed by the assistant.*
