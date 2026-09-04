# S224_DOCTERZ_TILE_NAMES — the Docterz tiles say Docterz

**The owner, 04-Sep-2026:** "the Docterz tiles' titles should be clear — 'Day', 'Daily', 'Clinic'
replace with 'Docterz'; keep the descriptions; in the Day Revenue tile replace 'takings' with
'collection'; the Daily Register tile → 'Docterz daily collection', and in its description replace
'The counters' with 'Reception'."

| tile (S223) | now | description before | description after |
|---|---|---|---|
| 📈 Day Revenue → `/finance/clinic/day` | **Docterz Revenue** | Clinic takings by day — from Docterz | Clinic **collection** by day — from Docterz |
| 📒 Daily Register → `/finance/clinic/register` | **Docterz daily collection** | The counter's day totals — cash, UPI, card | **Reception's** day totals — cash, UPI, card |

Six lines of `portal.py` change: the two names, the two descriptions, and the two `_TILE_GROUP`
keys (the map is keyed by name and the portal asserts every tile is grouped at import — renaming
the tile alone would 503 the portal). `tile_grants.json` v7 carries the same two names for the
same five people; grants match tiles by name, so **the two files move together** — with a stale
v6 the four staff logins would silently lose both tiles (measured in the selftest, §7).

**Not touched:** `Daily Collection` (`/finance/clinic/entry`) and `Clinic` (`/finance/clinic/review`)
are the S182 manual clinic-entry tiles, fed by the counter, not by Docterz — they begin with
"Daily"/"Clinic" but are not Docterz tiles. If the owner wants those renamed too, that is a
separate ruling. Every other tile is byte-identical (checked, 39 of them).

## Files
- `patch_portal_docterz_names_s224.py` — argv = the live md5; five exact anchors, each once; refuses otherwise; idempotent ("ALREADY PATCHED"); timestamped backup `portal.py.bak_S224_dznames_*`; compile-with-restore; prints NEW PIN.
- `tile_grants.json` — v7.
- `selftest_docterz_names_s224.py` — rebuilds the LIVE `portal.py` (3530f637…) from the repository chain, applies the patcher, and proves: anchors once, refusals, idempotence, the ruling word for word, `_TILE_GROUP` assert, 48-combination visibility walk unchanged but for the names, grants v7 = v6 + renames, fail-closed without grants, no ten-digit run, LF. `EVIDENCE_selftest_s224.txt` is its output: **59/59 GREEN**.
- `INSTALL.txt` — the one paste, with self-rollback. `PREDICTED_PINS.txt` — exact, not estimated.

Run the selftest from inside this folder: `python3 -B selftest_docterz_names_s224.py`.
