# S243_SCREEN_FIXES -- two portal screens, fixed where the screen's own code was wrong

Built 12-Sep-2026 (S243). Read-only investigation first; no gate is widened; no table touched.

## What it fixes

| # | screen | symptom (owner's browser, signed in as the doctor) | cause | fix |
|---|---|---|---|---|
| A | `https://followup.dr-manoj.in/finance/purchase/` | Flask 404 (the tile's `/finance/purchase/page/hub` works) | the purchase blueprint has no root rule: every rule is `/page/...`, `/api/...`, `/salts.*` | one new rule `"/"` (strict_slashes off) -> 302 to `/finance/purchase/page/hub`. Rev 14 over rev 13 `8090ca20`. |
| B | `https://followup.dr-manoj.in/finance/daily` (tile "Daily Sale") | redirected straight back to `/portal` | `page_daily` is the MAKER's day-entry form (Darpan); `require("maker")` refuses the doctor -- medical's CHECKER, never its maker (S179, schema seed) -- and the handler turns that 403 into a bare redirect to the portal | **owner's decision (S243): the maker gate stays.** A login holding `checker` on medical is sent to `/finance/review` (his console) instead of the portal; everyone else exactly as before. |

No other non-API route in finance_app.py bounces a checker this way (grep: `/finance/daily` is the only page gated `require("maker")` alone).

## Install (one line, on the VPS)

```
bash /root/deploy/repo/deploy_kits/S243_SCREEN_FIXES/install_S243_SCREEN_FIXES.sh
```

The installer: SUMS + KIT_ID gate -> refuses unless `/root/finance/purchase_app.py` is `8090ca20...` and
`/root/finance/finance_app.py` starts `f002defb` (S243_AUTOAPPLY, installed 13-Sep; history `81db4854` S240 -> `72bc8323`
S241 -> `f002defb`; the S243_AUTOAPPLY patch text applied to the S204_C2 base leaves the `/finance/daily` anchor at count 1)
-> `.bak_S243_<pin8>` of both -> purchase_app via `.new` + md5 + `mv`; finance_app
patched ON THE BOX by `patch_finance_daily_s243.py` (anchor must occur exactly once in the live bytes, else
refused with nothing changed) -> `py_compile` both (`/root/wa/venv/bin/python3`, fallback `/usr/bin/python3`)
-> `import finance_app` under the unit's own environment (read from `systemctl show`, drop-ins included; the
interpreter is the unit's `/usr/bin/python3`) -> restart `clinic-finance` only if the smoke passes -> healthz
within 20 s. Any RED after placing restores both files (and restarts if it had restarted). Re-run: ALREADY INSTALLED.

Predicted pin after install: `/root/finance/purchase_app.py` **`ad1fc00466458897751df7c9e9fcb99d`**.
`/root/finance/finance_app.py` is patched in place, so its pin is only known at install -- the installer prints it; record it.

## Rollback (one line each; `<pin8>` is printed by the installer, e.g. 8090ca20 and f002defb)

```
\cp -f /root/finance/purchase_app.py.bak_S243_8090ca20 /root/finance/purchase_app.py && \cp -f /root/finance/finance_app.py.bak_S243_<pin8> /root/finance/finance_app.py && systemctl restart clinic-finance.service
```

## Walks (offline, both green -- EVIDENCE_S243.txt)

- `walk_purchase_root_s243.py` -- rev 14 mounted on a real Flask app with the S224/S240 selftest's init signature: bare prefix with and without slash -> 302 to the hub; hub, salts and api/healthz byte-identical to rev 13; rev 13 reproduces the 404. 16/16.
- `walk_finance_daily_s243.py` -- the real finance_app imported as gunicorn imports it, real front gate, real unit_role, on a db copy: maker 200, checker -> /finance/review, stranger and anonymous -> portal, approvals still shut to the maker. 8/8 on the patched S204_C2 base; the unpatched base reproduces the symptom.
- On the box after install (touches no live file; copies the db first): `FIN_DIR=/root/finance /root/wa/venv/bin/python3 -B /root/deploy/repo/deploy_kits/S243_SCREEN_FIXES/walk_finance_daily_s243.py`

## Files
KIT_ID.txt · README.md · SUMS.md5 · EVIDENCE_S243.txt · install_S243_SCREEN_FIXES.sh · purchase_app.py (rev 14) ·
patch_purchase_root_s243.py · patch_finance_daily_s243.py · walk_purchase_root_s243.py · walk_finance_daily_s243.py

Tile note: "Daily Sale" is shown to the doctor by `roles ["doctor"]` (S223 fail-safe) and by name in tile_grants.json
(`manoj.extra`). Nothing in the portal moves in this kit; after B the tile lands him on Review.
