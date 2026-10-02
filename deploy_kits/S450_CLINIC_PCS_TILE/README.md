# S450_CLINIC_PCS_TILE — the PC kits on the server, one tile, one button per PC (session 290, 02-Oct-2026, D660)

**The owner, 02-Oct-2026:** "The agent kit you have parked in the Google Drive is a buried location and I think a better
place will be a server and a tile on my portal for all these kits which will be rarely required and the kit should be
self-sufficient to do an install after the Windows reinstall. This should be applicable to the current kits in the
medical PC, my PC, the reception PC and the future ones …" — "I log in into my portal in that PC in the browser. And
from there, I, by a very simple click, run and install the agent in that PC." On the mock: "looks good to me. Go ahead."

## What he sees
The tile **Clinic PCs** (Admin section, his login only) opens `https://followup.dr-manoj.in/finance/pcs`: one card per
clinic PC — Reception PC, Medical PC (Sanjeevni), Dr Manoj's PC — each with **Working / Needs a look / Not working / No
report** and the health page's own sentence for that machine; Shavez's PC and the Pathology lab PC as "Not set up yet".
A PC whose kit is on the server has one button, **Set up this PC as the …**. Today that is the Reception PC. The other
two show their state and say their kit is being packed — never a button that cannot work.

## What the button does
It hands the browser one small file, `ClinicSetup_Reception.cmd`, carrying a one-time code (60 minutes, that PC only;
the server keeps only its SHA-256). Keep, Run. The file then: fetches the kit and (on a bare PC) the bundled Python from
this server with the code · holds both to the md5s written into it · unpacks · runs the kit's own installer
(`INSTALL_RECEPTION_AGENT.bat`, rehearsed 02-Oct) · runs the agent's `--enroll <code>`, which gives the server that
PC's **new public** upload key and posts one signed heartbeat · says DONE · offers the owner's read-only share
(`share_setup.cmd`) if it is not there. The page ticks Google Drive, Tailscale and the share from the PC's own heartbeat.

## What it places
| file | change |
|---|---|
| `/root/finance/pc_kits.py` (NEW) | the page, the button, the two doors, the code store (`pc_kit_codes.json`, mode 600) and its trail (`pc_kit_log.txt`) |
| `/root/finance/finance_app.py` `022a9b0e…` → `e8dbf77e…` | the two api paths in `PUBLIC_PATHS` (the module checks its own code) · the guarded mount · the mounts row = 27 |
| `/root/portal/portal.py` `ba61e35a…` → `1a9fb99d…` | the tile (roles `[]`, like Manage Users) · its section · the code-fallback grant to manoj |
| `/root/portal/tile_grants.json` `392e6d89…` → `f9441311…` | "Clinic PCs" in manoj's `extra`; version 32 |

The kit it serves is in the repository clone: `deploy_kits/PC_KITS/reception/kit.zip` (the files of
`deploy_kits/S448_RECEPTION_AGENT`, zipped so their Windows line endings survive git) and
`deploy_kits/PC_KITS/_shared/pyportable_3.11.9.zip`; `KIT_INFO.txt` names both md5s and the page serves nothing that
does not match them. A changed PC kit reaches the server at the next publish + any install line (every line pulls).

`/root/finance/reception_keys.txt` (S449) is now **data**: enrolment from the page replaces that PC's line and keeps
the previous file as `.prev`. Its Register pin is the bytes at install, not a promise.

## Install — one line, the owner's
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S450_CLINIC_PCS_TILE/install_S450_CLINIC_PCS_TILE.sh
```
Needs S449 installed (it pins `finance_app.py` at S449's bytes). Gates → pins → the walk on scratch copies (the finance
app, the portal without `portal_config.py`, a copy of `finance.db`; the chain a setup file runs, over real HTTP, ending
with the kit's own agent; the box as it is as the negative control) → backups → place → restart `clinic-finance` and
`clinic-portal` → both doors' own refusals read back. Anything red after placing restores every file. `DRY=1` places
nothing.

## Not proven by this kit's walk
The `.cmd` itself runs only on Windows. It is rehearsed on the reception PC after the install (through the agent's
Drive door, with a setup file from the owner's first press of the button), and the result is recorded in canon.

## Next, each as its own kit, each rehearsed
The Medical PC's kit (with the Sanjeevni side, which owns those files) and Dr Manoj's PC's kit → `deploy_kits/PC_KITS/`
and a `SETUPS` entry each; then Shavez's PC and the Pathology lab PC when they get an agent.
