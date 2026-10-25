# S646_PROCROOM_TILES — direct tiles to the procedure-room pages (kit S646, session S349, 25-Oct-2026)

**Why.** The Scan App chat's ask of 25-Oct, relayed by the owner at 07:40 IST: Shavez reached his morning screen *Kal ke procedures*
only through Asset Register and the scan app's menu, and the owner reached his *Procedure room* through Assets & papers > Asset
Register > menu — too many steps, and the names did not say what they open.

**What changes.**
1. `/root/portal/portal.py` 6470f894 → 844166b1 (3 counted edits, `make_s646.py`): two tiles after *Parchi desk* —
   **Kal ke procedures** (`/scanapp/procroom/morning`, group Patients) and **Procedure room** (`/scanapp/procroom`, group Assets &
   papers), both doctor tiles by role; the Assets & papers face now reads *Asset register · procedure room · scan a bill · forms*.
2. `/root/portal/tile_grants.json` v38 → v39 (025f8ab9): *Kal ke procedures* granted to shavez by name; both new tiles masked for
   bhawna — only the two people the ask named get a new tile. The Sanjeevni chat's v38 lines are carried byte-for-byte.
The procedure pages (`/root/assetapp/procroom.py`) are the Scan App chat's and are not touched. No data step; restarts clinic-portal.

**Proven.** `walk_s646.py` 10/10: the real portal code, live and new, draws every login's home under every role; the only
differences are the two tiles where they belong (Shavez: Kal ke procedures; the owner: both; Dr Bhawna: neither). `--old` on
the live files: 6 S646 red, 0 older red.

## Install (on the server)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s646kit && cp -rp /root/deploy/repo/deploy_kits/S646_PROCROOM_TILES /tmp/s646kit && bash /tmp/s646kit/install_S646_PROCROOM_TILES.sh
```
## Undo
```
for f in portal.py tile_grants.json; do \cp -p /root/portal/$f.bak_S646 /root/portal/$f; done; systemctl restart clinic-portal
```
