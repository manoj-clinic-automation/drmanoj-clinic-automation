# Kit S187_D1a — Daily Flow v2, stage D1: the Day Page + the approvals surface (D326)

**Session 187 · 18 Aug 2026 · read-only stage: no schema change, no migration, no data write.
The only writing route touched is the EXISTING approve, reused as-is.**

## What ships

| file | md5 | what |
|---|---|---|
| `finance_app_D1a.py` | `cd3faaa4b30397f573d48bacf659bcf7` | `/finance/api/day/<date>/full` — declared · Marg bills→drug lines · ICICI settled-vs-declared · Yes Bank deposits · flags · exceptions · review · attribution, one checker-only call, variance chip at the measured ₹2,000 threshold. `/finance/api/approvals` — the strip where **every count carries its rows**. `/finance/approvals` — the page route. Built on the just-installed `81c26653…` bytes. |
| `finance_approvals.html` | `3798f9f7765b6c541582d61ff0731793` | your landing: chips (grey = zero, coloured = click-through) → approval queue → expand a day in place → bills click open to drug lines → Approve right there, UPI-mismatch acknowledgment preserved as a typed reason. The four live variance days (3 May, 9 May, 2 Jun, 12 Jun ₹8,487) stand as chips until cleared. |
| `live_pins_D1a.txt` | — | Register v5.15; exactly two rows moved (the app + the new page). PENDING until the close. |
| `KB_Register_v5_15_S187.md` | — | provenance; canonical at the close. D326 recorded (the three owner rulings + the staging). |

## Proof

Offline **371/381 = M1a's 359 + 12 new checks, zero failures added** (F-87; same 10 seed-state fails,
byte-identical). Installer rehearsed: RED path restored the app byte-perfect AND removed the new page —
nothing half-installed, service untouched.

## Expected on the box

Gates → selftest **~387/387** → service answering → pins **43 / 0 / 0, AMBER (pending)** →
**your new page: `/finance/approvals`**.

## What this stage deliberately does NOT touch

Darpan's screens (D2, when you're ready to walk him through it) · any edit surface or the Staff
Ledger bridge (D3 — **gated on the backlog-6 box check of the ₹70,000 claim**) · home/procedure
medicine (D4) · the Yes Bank auto-feed from your personal Gmail (D5).

## Install

PC: `deploy_kits\S187_D1a\PUSH.bat` → VPS: `bash /root/deploy/vps_deploy.sh S187_D1a`
