# S224 LIVE TOOLS — the manojz-side files this session changed, captured from their LIVE paths

**A11:** a session that touches a PC captures the bytes that are RUNNING and compares them against the
live source, not against the kit's own sums. Every file here was copied from its live path on `manojz`
at the S224 close (04-Sep-2026, midday IST) and hashed there; `VERIFIED_AGAINST_LIVE.md` beside this
file is that comparison, both ways.

## What is in the kit, where it lives, and what it does

| kit path | live path on manojz | what it is (S224 paper) |
|---|---|---|
| `margsync\MargPull\marg_router.py` | `D:\Downloads\margsync\MargPull\marg_router.py` | the Marg report router; **A4 / F-235 closed** — `stock_variant()`: ORTHOTICS / SUBSET / EXPIRED / NEAR / MIXED, `index.csv` `notes` column (`S224_A4_F235_VARIANT_NAMING`) |
| `margsync\MargPull\marg_rescan.py` | `D:\Downloads\margsync\MargPull\marg_rescan.py` | the rescue path for `_REFUSED`; `rejudge()` calls the router's own variant rule |
| `margsync\MargPull\signatures.json` | `D:\Downloads\margsync\MargPull\signatures.json` | the report registry; **A1** — `SALE_RETURN / SUMMARY` added (`S224_SALE_RETURN_SUMMARY_SIGNATURE`) |
| `margsync\MargPull\pull_watchdog.py` | `D:\Downloads\margsync\MargPull\pull_watchdog.py` | **A3 NEW** — the pull-asleep detector (`S224_MANOJZ_PURCHASE_LEG_AND_WATCHDOG`) |
| `margsync\MargPull\PULL_WATCHDOG.bat` | `D:\Downloads\margsync\MargPull\PULL_WATCHDOG.bat` | **A3 NEW** — the scheduled wrapper for the watchdog |
| `margsync\PUSH_STOCK_NIGHTLY.bat` | `D:\Downloads\margsync\PUSH_STOCK_NIGHTLY.bat` | **v2** — three steps: Marg's figure · our computed figure · vendors + feed, then all purchases |
| `margsync\PUSH_STOCK_DAILY.bat` | `D:\Downloads\margsync\PUSH_STOCK_DAILY.bat` | **A2** — `BASELINE` moved to `03-09-2026` |
| `margsync\PUSH_PURCHASES_NOW.bat` | `D:\Downloads\margsync\PUSH_PURCHASES_NOW.bat` | **NEW** — the owner's one double-click: verify the token, then push every archived purchase export |
| `deploy_kits\S208_STOCK_LEDGER\push_expected.py` | `D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\S208_STOCK_LEDGER\push_expected.py` (run in place) | **A2** — `bill_dates()` reads BILL WISE as well as SUPPLIER WISE |

Not captured here, deliberately: `push_purchases.py` and `marg_purchase_rows.py` are run in place from
`deploy_kits\S224_MARG_PURCHASES\` (already in the repository under that kit's own `SUMS.md5`);
`marg_relabel_s224.py` was a one-off (its `--apply` ran once; kept beside the router, pinned in the
Register); `index.csv` and `_stock_universe.json` are data, not tools.

## Install order (a bare `manojz`, from a clean repository checkout)

1. `signatures.json` → `D:\Downloads\margsync\MargPull\` (the router refuses reports it cannot classify; the registry goes first).
2. `marg_router.py` and `marg_rescan.py` → `D:\Downloads\margsync\MargPull\` **together** — the new router writes a 16-column `index.csv`; the old rescan under the new index would misalign rows.
3. `push_expected.py` → `D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\S208_STOCK_LEDGER\` (the daily and nightly `.bat` files run it from there with `python -B`).
4. `PUSH_STOCK_DAILY.bat`, `PUSH_STOCK_NIGHTLY.bat`, `PUSH_PURCHASES_NOW.bat` → `D:\Downloads\margsync\`. The nightly's step 3 needs `deploy_kits\S224_MARG_PURCHASES\` present in the repository checkout, else it logs `STEP 3 SKIPPED` and never says Done.
5. `pull_watchdog.py` and `PULL_WATCHDOG.bat` → `D:\Downloads\margsync\MargPull\`.
6. Register the scheduled tasks (below). Then one live cycle: wait for the 10-minute pull, read `D:\Downloads\margsync\MARG_PICTURE.txt`.

Every `.bat` here is CRLF (F-294); every `.py` is LF. Copy bytes, never re-type.

## Credentials NEEDED (never values — nothing secret is in this kit or the repository, F-185 / F-31)

- **The Marg push token**, read by `push_purchases.py` and `push_snapshot.py` from
  `\\<medical PC>\DDrive\SendToClinic\token.txt` with a local cache at
  `D:\Downloads\margsync\SendToClinic\token.txt`; sent as the `X-Finance-Marg` header (F-237: never
  `X-Finance-Cron`). Same token, same reader, for every push in this kit.
- **The vendor contact pairs**, `D:\Downloads\margsync\_config\stockist_phones.json` (`"pairs"`: name →
  number), read by `push_purchases.py --vendors`. Lives in `_config\` only; the repository holds no number.
- The Tailscale reach to the medical PC for the 10-minute pull itself (`PULL_FROM_MEDICAL.bat`, S203 kit —
  unchanged this session).

## The scheduled tasks on manojz (all run as the owner's interactive account)

| task name | runs | schedule | note |
|---|---|---|---|
| `Marg pull from medical` | `D:\Downloads\margsync\MargPull\PULL_FROM_MEDICAL.bat` (via `PULL_HIDDEN.vbs`) | every 10 min | S203; unchanged this session |
| `MargPullWatchdog` | `D:\Downloads\margsync\MargPull\PULL_WATCHDOG.bat` | every 15 min | **NEW at S224 (A3)** |
| `Clinic stock nightly` | `D:\Downloads\margsync\PUSH_STOCK_NIGHTLY.bat` | 22:30 daily | S221; v2 this session |

**F-314, found this session:** every one of these tasks had been created with the `schtasks` default
*"start the task only if the computer is on AC power"* — the laptop on battery put the pull to sleep
three times in one month (06:40 → 08:37 on 04-Sep; S219's 46 minutes). **The battery flags were
cleared on all three by the owner's PowerShell line on 04-Sep-2026.** Any re-registration must clear
them again — a task created by `schtasks` starts only on AC until told otherwise.

Registration line for the watchdog (the only one new this session):

```
schtasks /Create /TN "MargPullWatchdog" /TR "\"D:\Downloads\margsync\MargPull\PULL_WATCHDOG.bat\"" /SC MINUTE /MO 15 /F
```

— followed by clearing the battery conditions on it, as on the other two.

## Verification

`SUMS.md5` was written LAST, from inside this folder, and verified there (`md5sum -c SUMS.md5`).
`VERIFIED_AGAINST_LIVE.md` records each captured file's md5 against its live source path — both ways —
at the moment of capture. A kit verified only against its own copy proves nothing about what is running.

---
*Captured at the S224 close, 04-Sep-2026. Papers: `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S224\`.*
