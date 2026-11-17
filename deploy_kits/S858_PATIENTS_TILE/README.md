# S858_PATIENTS_TILE — a tile of its own for the Patients page (the parent, S478, 17-Nov-2026) — D997 item 3

**His ask (17:10 IST 17-Nov):** a portal tile of its own for the Patients page — until now reached only from the command
console's "The month" section.

**The change.** A NEW tile **Patients — month by month** (`/finance/console/patients`; small line: new and returning ·
revenue · front desk · Google) — a doctor tile by role in `/root/portal/portal.py` (8f60b310 → cb37c7fb), alone in its own
group "Patients by month", so his folded home draws it **flat, as a tile, right after the Patients folder** (a folded group of
one is drawn flat — S586's own rule). `/root/portal/tile_grants.json` (v46 → v47, b7b1fabf → 8299e8d4) only places that group
after Patients in manoj's own order; nothing granted or masked. The page's own gate is the console's (owner only), unchanged.

**Proof.** `walk_s858.py` (S816's method: the portal's own tile code from each file, run on its own) — for every role ×
every login in the grants file × phone/clinic PC, everything else is drawn exactly as before; the tile only for the doctor
role; his home: right after Patients, flat; Dr Bhawna's "only" list keeps hers unchanged; the no-grants fallback still
places it; the grants file differs only in manoj's order, the version and the note, in its own format (12/12). Control: the
live files as both go red. The installer (S816's pattern) checks the doors before and after the restart, the journal, and
puts both files back on any red.

**Install** (after the publish): the S478 combined line, or alone:
`cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s858kit && cp -rp /root/deploy/repo/deploy_kits/S858_PATIENTS_TILE /tmp/s858kit && bash /tmp/s858kit/install_S858_PATIENTS_TILE.sh`
Undo: `bash /tmp/s858kit/install_S858_PATIENTS_TILE.sh --undo`.
