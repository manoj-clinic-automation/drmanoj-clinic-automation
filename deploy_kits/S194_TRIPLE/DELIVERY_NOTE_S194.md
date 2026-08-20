# S194 — Daily Sale v2 · Home-medicine · Cash/UPI reclass  (ONE install run)

Three medical-finance features, built offline against the **current live bytes**
(hash-verified: finance_app `4c0a2d19`, finance_ingest `a4e9663f`,
finance_approvals `8ce3fabd`) and bundled into a single gated installer.

## What lands
- **⭐1 Daily Sale v2** — a NEW two-stage page at **`/finance/daily`**
  (enter+save → submit → reconcile + transfers → final submit, plus a
  transfer-only path). Same `POST /finance/api/day` contract as the proven
  page. **`/finance/entry` is untouched and stays as the fallback** — switch
  Darpan over only when you're happy.
- **⭐2 Home-medicine bills** — any Marg bill made out to *Home Medicine /
  Home Medisun* is auto-tagged (`sale_item.home_med`) on ingest — no scan, no
  manual entry — and totalled on a new Hub card + `GET /finance/api/home-medicine`.
- **⭐3 Cash/UPI reclassification log** — when a day is re-loaded from Marg and a
  bill's mode flips (cash↔upi), it's written to a new `mode_change_log` table and
  shown on a new Hub card + `GET /finance/api/reclassifications`. Amir's counter
  conversions stop being silent.

## Install (one run)
```
cd <this kit folder on the box>
bash install_s194.sh
```
The installer: checks kit bytes → **currency-gates** the 3 live files →
baseline smoke (must be all-green) → backs up files + DB → idempotent DB
migration (adds `home_med`, creates `mode_change_log`) → installs the new page
→ swaps app/ingest/Hub → `py_compile` → **new smoke must be ALL-GREEN and the
S194 checks must have run (total grows)** → restart + verify. **Any red rolls
ALL files back** and restarts the service.

## Pin after GREEN (D321(d)) — the installer prints these
- `finance_app.py`        → `87cf456866237c2634c405e3dc3b8a61`
- `finance_ingest.py`     → `6cb83302b022ca3d46a53b32011a7ddd`
- `finance_ui/finance_daily.html`     → `e1092757bcad6cfbc74473422741af8e`
- `finance_ui/finance_approvals.html` → `402fa7b263b86f75bfccc122f1a0ca37`

## How it was verified offline
The box `--selftest` copies the live DB (F-87), so it can't run fully offline;
it was run on the F-87 seeded-shape store up to the (unrelated, unseeded) clinic
section, and **14 targeted checks** proved every S194 path: the page serves to a
maker and is refused to a checker; both endpoints answer for maker+checker and
refuse anon; a *Home Medisun* bill tags `home_med=1`; and a cash→upi re-import
logs exactly one flip. The **box install-gate runs the full smoke on the live
DB** (clinic included) as the authoritative check, with rollback — so a red is
safe, not a live break.

## Next
⭐4 (record Bhawna/Manoj hand-overs as `cash_movement`s) comes next — once it's
in, the Daily page's drawer and the Hub reserve track live from the flow.
Note for ⭐2: bills are matched by the customer text containing "home medi"
(covers *Home Medicine* and *Home Medisun*); tell me if Marg uses a different
exact spelling and I'll widen it.
