# S243_DARPAN_TILE — Darpan's day gets its door

**The owner, 13-Sep-2026:** Darpan's day now lives at `/finance/darpan/kal` — *"Kal ka hisaab"*, kit
`S243_DARPAN_KAL`: yesterday's Marg report fills the numbers, he types two things (kitna cash diya,
kisko diya) and answers yesterday's flagged returns. **His tile must open it.** And the CA's ruling
retired "Corrections" as his task.

## What was wrong

`/finance/darpan/kal` has **no tile**. Like `/finance/amir` at S242 and `/finance/reports/aaj` this
morning, a page with no tile can only be reached by typing the address. Darpan's Money & Accounts
section today reads *Daily Sale · Vaapsi Desk* — the manual form, not his day.

## What changes

**One tile is added.** `Kal ka hisaab` 🧮 → `/finance/darpan/kal`, *"Kal ka cash — kitna diya,
kisko diya"*, section *Money & Accounts*, placed **immediately before Daily Sale** so it is the first
money tile he sees. `roles: ["doctor"]` like every other granted tile — a lost or malformed grants
file leaves it with the doctor and nobody else. Darpan is given it **by name** in
`tile_grants.json` v14.

**Why a new tile, not a repoint.** A tile has one address for everybody. *Daily Sale* is the owner's
too — his now lands on Review (`S243_SCREEN_FIXES`) — so repointing it would move **his** door.
Daily Sale stays exactly as it is for everyone, Darpan included: the manual form is the fallback.

**Corrections — nothing to withdraw.** It was checked, not assumed: *Corrections* is
`roles: ["doctor"]` and is granted by name to nobody in v13. Darpan is not shown it today and is not
shown it after. The page stays reachable by address and for the owner. No line moves for it.

**Nothing is removed or moved.** Every other tile keeps its roles, address and place; every other
login's grants are byte-equal to v13. The pages' own gates are untouched — this decides what he is
*shown*, not what he may *reach*. Darpan's Money & Accounts after: **Kal ka hisaab · Daily Sale ·
Vaapsi Desk**.

## Pins — two files, and they move together

| file | from | to |
|---|---|---|
| `/root/portal/portal.py` | `4bb6bde0e2e07033ac0e0f5d7a7daaf6` (after S243_REPORTS_TILE) | **`06f1b378608fbc97c54bc1f546d7985c`** |
| `/root/portal/tile_grants.json` | `c9ee95c39bb805086b79d95327b2b626` (v13) | **`0efad736e71de7199e7c596a5b3d0c2e`** (v14) |

The installer gates both, exactly. **S243_REPORTS_TILE must be installed first** (it produces the
from-pin). A grant matches a tile by **name**; the two files are placed in the same step.

## Proof

**`EVIDENCE_S243.txt`** — the live `portal.py` was **reproduced, not read**: the S243_REPORTS_TILE
patcher applied to the 13-Sep capture (`d08721f6`) gives `4bb6bde0`, the box's pin. The walk
(`walk_darpan_tile_s243.py`) patches that file in memory, imports it (the portal's own "every tile
is grouped" assert is the gate) and asks **portal's own `_visible_sections`** what each person is
shown — with v14, and again with the unpatched file + v13 as the **baseline**, so "unchanged" is a
comparison. **52 checks, all green:**

- darpan sees `Kal ka hisaab` → `/finance/darpan/kal`; no `Corrections` before or after; his other tiles unchanged
- manoj sees everything he saw, plus the one new tile, `Corrections` and `Daily Sale` included
- shavez, amir, alisha, shivani, bhawna, a bare staff login: unchanged tile for tile, section for section
- Daily Sale and Corrections tiles byte-for-byte what they were; every other tile too; only additions (11 lines)
- v13 → v14: version, note, darpan.extra only; 12 other logins byte-equal
- fail closed: no grants file, or a malformed one → darpan loses the tile, the doctor keeps it

Installer mock-tested on a throw-away ROOT (`mock_install_darpan_tile_s243.sh`, **17/17**): wrong
portal pin refused · wrong grants pin refused · install lands both predicted pins with two
`.bak_S243_<pin8>` · ALREADY INSTALLED on re-run · health failure → both restored, restarted on the
restored files · **smoke failure → both restored and the service is never restarted**.

## Install — one line on the VPS, after the publish

```
bash /root/deploy/repo/deploy_kits/S243_DARPAN_TILE/install_S243_DARPAN_TILE.sh
```

Gates: SUMS + KIT_ID → live pins → patch on a copy (must hash to `06f1b378`) → `py_compile` →
backups → place → import smoke (tile present, grants v14, darpan shown it, no Corrections for him,
the doctor keeps everything) → **only then** `systemctl restart clinic-portal` → `/portal/health`
200 within 20 s. Any RED after placing: both files restored, exit 1. Re-run: ALREADY INSTALLED.

## Reverse — one line each

```
\cp -f /root/portal/portal.py.bak_S243_4bb6bde0 /root/portal/portal.py
```
```
\cp -f /root/portal/tile_grants.json.bak_S243_c9ee95c3 /root/portal/tile_grants.json
```
```
systemctl restart clinic-portal
```

## After install

Nothing for the owner. Darpan opens the portal and taps **Kal ka hisaab**:

```
https://followup.dr-manoj.in/finance/darpan/kal
```

The owner's own login sees the same tile by role; the page shows him the English owner view.

## Files

| file | what |
|---|---|
| `patch_portal_darpan_tile_s243.py` | two anchors, count==1 each, MARK-idempotent, prints from/to md5 |
| `tile_grants.json` | v14, full file |
| `walk_darpan_tile_s243.py` | the live-shape walk (`PORTAL_PY=... python3 -B walk_darpan_tile_s243.py`) |
| `install_S243_DARPAN_TILE.sh` | the installer |
| `mock_install_darpan_tile_s243.sh` | the installer's proofs on a throw-away ROOT |
| `KIT_ID.txt` · `SUMS.md5` · `EVIDENCE_S243.txt` | identity, hashes, proof |
