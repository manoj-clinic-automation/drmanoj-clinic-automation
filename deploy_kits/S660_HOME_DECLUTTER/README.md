# S660_HOME_DECLUTTER — the owner's home: three old tiles gone, whose screen on each staff tile, one new tile · the parent · session 357 · 26-Oct-2026

**For the owner, in three lines.** Three tiles leave your home only (their pages stay live for whoever uses them): **Clinic** (the old review-and-approve page, last used 5-Oct), **OPD & X-ray/Proc Slips** (the old slips page the Parchi desk replaced) and **Clinic Gist** (your Today tile and console carry it). **WhatsApp Approvals** (MyOperator's vendor panel) moves into the System folder. In every folder, a tile that is a staff member's screen now says whose — Parchi desk · Shavez, Kal ke procedures · Shavez, Physiotherapy · Bhati, Petty book · Bhati, Check karein · staff, Report baaki · staff, Docterz daily collection · reception — the way the Sanjeevni folder already does. One new tile, **Attendance correction**, in the Staff folder (the month-end flow, D786, from 1-Nov). Call Tracker stays (your word). The Sanjeevni chat's in-place folders (S657) are kept exactly. Nobody else's home changes.

## Why
The owner's words, 26-Oct-2026: *"need you to do same for whatever other tiles possible, and retire old irrelevant tiles to declutter it ... answer me before any build"* (06:36); on the analysis: *"Leave 3 as such for now [Call Tracker], and the new accordion style developed by sanjeevni project is fine to keep, build it"* (07:19). The live-numbers-on-folder-faces idea in the analysis was dropped in the build: the top row already carries those numbers; a second copy on the faces would be the same figure twice.

## Files — FROM (S657's TO) → TO; built ON the Sanjeevni chat's S657 bytes, after its install
| live file | owner | FROM | TO | what |
|---|---|---|---|---|
| `/root/portal/portal.py` | **the parent** | 5f4f3738 | fe9cc368 | 3 counted edits: `_TILE_GROUP["WhatsApp Approvals"]` → System; the *Attendance correction* tile after *Salary — approve & lock* (+ its group row); `S660_WHO` and one line in `_home_blocks` labelling a FOLDED folder's staff screens (display only; a flat list — every staff login — is untouched) |
| `/root/portal/tile_grants.json` | **the parent** | 171f94f8 | 83828b81 | v40 → v41: manoj `mask` + *Clinic*, *OPD & X-ray/Proc Slips*, *Clinic Gist*. Every other login byte-for-byte as v40 (proven: the whole JSON differs only in `version` and `users.manoj.mask`) |

**Requires S657 installed** — the FROM pins are S657's TO; the installer stops otherwise. No data step, no crontab change, `clinic-portal` restarted alone.

## Proven (S357, in manojz's VM, python3 + flask; on S657's TO bytes rebuilt from the 26-Oct bundle)
`walk_s660.py` **12 of 12 green**: his home (the three gone; Attendance correction in Staff; WhatsApp Approvals in System and not in Calls; the seven who-labels; every other tile where it was; the two Sanjeevni folders exactly S657's) · **every other login under every role draws the same tiles in the same folders** (15 logins × 3 roles; the two added/moved tiles reach no real login but his — the doctor ROLE tried on other names sees them; Dr Bhawna's `only` list hides them) · the rendered home (the tile's door `/register/attcorr`, 12 who-labels, S657's panels, no sheet, no Back) · Shavez's rendered home unchanged. **Control** (`--old`: the base files as under test): 7 S660 red · 0 older red · 5 green. **The installer rehearsed on a made-up root** (stubbed systemctl/curl): DRY green; the full run placed, read back, restarted, released the lock and removed its OFF switch; run again → ALREADY INSTALLED.

## Install (on the server, after the publish AND after S657; the window is 08:02–23:49 IST)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s660kit && cp -rp /root/deploy/repo/deploy_kits/S660_HOME_DECLUTTER /tmp/s660kit && bash /tmp/s660kit/install_S660_HOME_DECLUTTER.sh
```
## Undo (the installer prints it with the exact backup names)
```
\cp -p /root/portal/portal.py.bak_S660_5f4f3738 /root/portal/portal.py && \cp -p /root/portal/tile_grants.json.bak_S660_171f94f8 /root/portal/tile_grants.json && systemctl restart clinic-portal
```
