# S243_AMIR_VISIT -- the salt-list prompt, and "Amir's visit -- what was done"

Built 13-Sep-2026 (S243) to the owner's ruling of the same day:

> (a) after Amir's visit-day work, once his salt tasks are ticked, the system asks HIM to generate the
> SALT WISE ITEM LIST export from Marg and keeps it raised to him (red) and to the owner (amber) until
> the server sees the list arrive. (b) a readable "Amir's visit -- what was done" summary on the owner's
> own page, collapsed/expandable, in one place.

## What changes

**`/root/finance/amir_day.py` -- replaced whole** (the kit's file is `patch(live)`; the patcher proves that
byte-for-byte on the box before anything is placed):

| where | what |
|---|---|
| step 6 (Salt / naam) and the close screen (step 7, both "Din band karein?" and "DIN BAND") | a **red** line *"Marg se SALT WISE ITEM LIST nikaalo -- yahan khud tick ho jayegi"* with the time of the last list, whenever salt tasks have been ticked after the last list the server saw; turns **green** *"SALT WISE ITEM LIST aa gayi HH:MM"* once a newer list is seen. He is never asked whether it arrived. |
| what "seen" means | a `mi_file` row of type `SALT_WISE_ITEM_LIST` (marg_ingest writes it the moment the one door takes the file, S240) newer than his last tick. Times are read from marg_ingest's `stamp` (Marg's YYYYMMDD-HHMMSS) else `received_at`. `salts_refresh.py`'s state file (`/root/finance/salts_refresh.state.json`, env `SALTS_REFRESH_STATE`) adds the "salts page refreshed HH:MM" detail. |
| the gate | **unchanged**: `GATE_STEPS = (2, 4, 5, 6)`, `done[6]` is his tap alone, `_left()` never names the list. The day closes with the list still awaited -- the prompt stays raised on the DIN BAND screen (walked). |
| `/finance/amir/day` (the owner's English page) | a card **Salt list from Marg** -- amber *"Waiting for Marg's SALT WISE ITEM LIST -- N salt tasks ticked since the last list (last list dd-mm HH:MM)"*, green *"Salt list arrived dd-mm HH:MM, after the day's N ticks"*, grey when there were no ticks; and a collapsed `<details>` **Amir's visit -- what was done**. |
| `/finance/amir/day/api/visit-summary?date=yyyy-mm-dd` (**checker only**, 403 to everyone else, anonymous -> portal) | JSON: `state` OPEN/CLOSED, `steps` (one verdict per step 1-7: done / skipped / not needed / partly / not yet / open, with a detail), `bills` (dispositions by reason), `reports` (purchase_export rows of the day: types, rows, Rs, time), `salts` (ticks by section, renames, who, sheet uploads), `claims` (raised that day, Rs), `salt_list` (the prompt's state with an English `owner_line`). |
| `/finance/amir/api/healthz` | `kit: S243_AMIR_VISIT` |

**`finance_ui/finance_approvals.html` -- patched on the box** (three anchors): inside the **Marg** card, after the
identity box, a collapsed `<details>` **"Amir's visit -- what was done"** that fetches the API for today; its
summary line grows *"· salt list awaited"* while the prompt is pending. Sits beside S243_AUTOAPPLY (already live)
and S243_DARPAN_KAL (installs before this kit); the three anchors are untouched by either and the patch was
proven in both orders.

**`finance_app.py` -- not touched.** amir_day has been mounted since S241; the new route rides on it.

## Found by the walk and fixed here (F-455 candidate, to mint at the close)

The live `_export_state()` and `_bills()` compare `substr(export_stamp,1,10)` with `yyyy-mm-dd`, but the
purchase door (`purchase_app` STAMP_RE) writes `export_stamp` as **`YYYYMMDD-HHMMSS`**. So on real data
step 4 ("Jaanch") could **never** verify the pair, and every bill of the day read as *"pichhla baaki"*.
The S241 fixture used a `yyyy-mm-dd hh:mm:ss` stamp, which is why 65 green checks missed it (`amir_day` has
one day and zero dispositions live -- consistent with a day that could not close). Since this kit replaces the
file whole, the fix rides here: `_export_day_sql()` reads both shapes; `_hhmm()` shows the time out of Marg's
stamp. Walk checks prove both shapes and the readable time on step 4.

## Install (the owner's double-click publishes; then ONE line on the VPS, in the quiet window)

```
bash /root/deploy/repo/deploy_kits/S243_AMIR_VISIT/install_S243_AMIR_VISIT.sh
```

Order: after `S243_SCREEN_FIXES` and `S243_DARPAN_KAL` (the hub gate accepts the plain `cc349dd0` page too, so
the order is not enforced -- but the walk was run on the post-both state). Refuses unless `amir_day.py` is
**exactly** `ae2c89398e3c1fa63f9dadcff9e69d84` (full-file replacement) and `finance_approvals.html` is
`cc349dd0…` **or carries the S243_DARPAN_KAL mark**. Writes `amir_day.py.bak_S243_ae2c8939` and
`finance_approvals.html.bak_S243_<pin8>`, places, py_compiles, import-smokes under the unit's environment
(blueprint + the new route must be registered), restarts `clinic-finance`, waits for healthz (20 s). Any RED ->
both files restored, service restarted. Re-run -> ALREADY INSTALLED.

**Predicted to-pins:** `amir_day.py` -> the kit's md5 (SUMS.md5); hub `cc349dd0` -> `e348a106c494e6094953226dd06de07f`,
or after DARPAN_KAL `7dbb5e56` -> `c12be75b8c357417c84581f96343eab7`.

Rollback by hand:
```
\cp -f /root/finance/amir_day.py.bak_S243_ae2c8939 /root/finance/amir_day.py && \cp -f /root/finance/finance_ui/finance_approvals.html.bak_S243_<pin8 printed by the installer> /root/finance/finance_ui/finance_approvals.html && systemctl restart clinic-finance.service
```

## Proofs in the kit

* `patch_amir_day_salt_prompt_s243.py --selftest <live> <kit>` -- 11/11: pin, thirteen anchors once each, compiles, only additions bar the four named lines, patch(live) == kit file.
* `patch_hub_amir_visit_s243.py --selftest <page>` -- 16/16 on the live page and on the DARPAN_KAL-patched page.
* `walk_amir_visit_s243.py` -- **70/70** live-shape: real finance_app f002defb patched in memory with SCREEN_FIXES + DARPAN_KAL, real sqlite from the schemas + mi_file, real hub page. Ticks -> red/amber/pending; newer mi_file -> green; a later tick -> pending again; the day closes with the prompt raised; API checker-only; anonymous -> portal; empty past day; missing tables; the export-stamp fix both ways; hub block + DARPAN_KAL card together; no 10-digit number in any page.
* `mock_install_amir_visit_s243.sh` -- the installer's six proofs on a throw-away ROOT.

On the box after install (builds its own db, touches nothing live):
```
FIN_APP=/root/finance/finance_app.py FIN_MODS=/root/finance SIBLINGS=/root/deploy/repo/deploy_kits /root/wa/venv/bin/python3 -B /root/deploy/repo/deploy_kits/S243_AMIR_VISIT/walk_amir_visit_s243.py
```

## Not in this kit

No new table, no schema change, no cron, no token, no phone number, no patient data. The claim queue for
Darpan (D471) and the Reports tile are separate kits.
