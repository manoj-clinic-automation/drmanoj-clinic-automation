# S838_SCANAPP_GOTO — Go to ▾ on the scan app's top bar

Board `_numbers` v1515 → v1516 · built in the Scan App chat, session 464, 14-Nov-2026 · his "FINAL" (20:32 IST) on the mock-up
https://claude.ai/artifact/JPVjEyijD9doKinJKgvDHY.

## What it does
The scan app's blue top bar keeps **Sorting desk (N) · The month · Bills awaited (N)** and one button, **Go to ▾ — every scan-app page**,
which opens the pages grouped, as the Sanjeevni Hub's Go to does:
1 · Papers coming in — Sorting desk, Add a paper from a file, Bills awaited, All papers ·
2 · Clinic purchases & stock — The month, Procedure room, Kal ke procedures, Stationery, Stationery sort, X-ray films ·
3 · Dealers — Implant stock ledger, Vendors, Sanjeevni Hub ↗ (the owner) ·
4 · Machines & renewals — Machines, Batteries, Renewals · 5 · Yours only — Admin, The switches.
The panel is built from the bar's own list (`asset_register._s559_items`): a person sees only the pages he already has; a page not placed
in a group appears under "Other pages". Click outside, Escape or "close ✕" shuts it.
**From the portal:** the Scan app tile → the home page → Go to ▾ → any page.

## How
`sorting_desk.py` only (FROM d49e48ff = S835's TO): the S838 block; at mount it registers a one-time step that, at the first request a
worker serves, takes over the bar's helper (`asset_register._s559_bar` and the Jinja global `s559_bar`) — the bar is defined after the desk
mounts. Any error draws the old bar. The switch **`bar.goto` — "Go to menu for Shavez"** (absent = OFF) on the desk's switch card: the
owner sees the new bar at once; a manager keeps the old bar until it is on. asset_register.py and every other file: read only, pinned.

## Proof
`walk_s838_app.py` on the real app: **9 green**, control on the live files **7 red** (A0, Z1 green both ways) · `walk_s838_page.js`
(headless DOM, the button): **5 green**, control **5 red** · `rehearse_s838.sh`: **7/7**.

## Install
    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S838_SCANAPP_GOTO/install_s838.sh

## Undo
The installer prints `\cp /root/assetapp/sorting_desk.py.bak_S838_d49e48ff /root/assetapp/sorting_desk.py` and the restart.

## Cold review
A separate reviewer: **SAFE TO INSTALL** (the takeover, the template and escaping, the panel on the desk page, what a manager sees). Its one
unread point -- a box around the bar in the main page shell -- checked: the bar sits directly in the page, nothing clips it.
