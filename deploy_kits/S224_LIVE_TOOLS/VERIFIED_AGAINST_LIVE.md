# S224 LIVE TOOLS — VERIFIED AGAINST LIVE, both ways, at capture (04-Sep-2026, manojz)

Way 1: kit copy → hashed; live source → hashed; equal or not. Way 2: the live source re-read and compared byte-for-byte against the kit copy (not only by digest). A row is a pass only when both say so.

| kit file | kit md5 | live path (as the device shell mounts it) | live md5 | digest equal | bytes equal |
|---|---|---|---|---|---|
| `margsync/MargPull/marg_router.py` | `fb32045c563b9fc64a7ce0fe8e9ef6e6` | `D:\Downloads\margsync\MargPull\marg_router.py` | `fb32045c563b9fc64a7ce0fe8e9ef6e6` | YES | YES |
| `margsync/MargPull/marg_rescan.py` | `36a0db97d8be357fba4a1d0cf42ed6e5` | `D:\Downloads\margsync\MargPull\marg_rescan.py` | `36a0db97d8be357fba4a1d0cf42ed6e5` | YES | YES |
| `margsync/MargPull/signatures.json` | `c0a3726861f861012b22bf765227c671` | `D:\Downloads\margsync\MargPull\signatures.json` | `c0a3726861f861012b22bf765227c671` | YES | YES |
| `margsync/MargPull/pull_watchdog.py` | `f0eb9f40a0cd06875aba107b12151a73` | `D:\Downloads\margsync\MargPull\pull_watchdog.py` | `f0eb9f40a0cd06875aba107b12151a73` | YES | YES |
| `margsync/MargPull/PULL_WATCHDOG.bat` | `212c37a2e94dcbd9ac4ee537b61fd9f3` | `D:\Downloads\margsync\MargPull\PULL_WATCHDOG.bat` | `212c37a2e94dcbd9ac4ee537b61fd9f3` | YES | YES |
| `margsync/PUSH_STOCK_NIGHTLY.bat` | `99d05e3f7f05d472413c864d1665ccea` | `D:\Downloads\margsync\PUSH_STOCK_NIGHTLY.bat` | `99d05e3f7f05d472413c864d1665ccea` | YES | YES |
| `margsync/PUSH_STOCK_DAILY.bat` | `73a0635ba6164ec8da8c8f61de9d3210` | `D:\Downloads\margsync\PUSH_STOCK_DAILY.bat` | `73a0635ba6164ec8da8c8f61de9d3210` | YES | YES |
| `margsync/PUSH_PURCHASES_NOW.bat` | `7b8d0370486cb13a877d0968f7f31bbe` | `D:\Downloads\margsync\PUSH_PURCHASES_NOW.bat` | `7b8d0370486cb13a877d0968f7f31bbe` | YES | YES |
| `deploy_kits/S208_STOCK_LEDGER/push_expected.py` | `47641a9381a1bbffd074d6a7af435a9d` | `D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\S208_STOCK_LEDGER\push_expected.py` | `47641a9381a1bbffd074d6a7af435a9d` | YES | YES |

**Result: ALL 9 OF 9 IDENTICAL BOTH WAYS.**

Where a working paper states the full md5 the kit value agrees with it: `marg_router.py` `fb32045c563b9fc64a7ce0fe8e9ef6e6` · `marg_rescan.py` `36a0db97d8be357fba4a1d0cf42ed6e5` · `signatures.json` `c0a3726861f861012b22bf765227c671` · `push_expected.py` `47641a9381a1bbffd074d6a7af435a9d` (checked by the Register build, which refuses on disagreement). The five `.bat` / watchdog values are the first full pins these files have had.

*Written before `SUMS.md5`; `SUMS.md5` is generated last and covers this file too.*
