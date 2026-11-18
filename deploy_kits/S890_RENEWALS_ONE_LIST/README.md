# S890_RENEWALS_ONE_LIST — every renewal on ONE list on the server (D1017) · the parent, S488, 18-Nov-2026

**His word (21:56 18-Nov):** the renewals live wholly on the server; the Google Sheets are not used; the personal Janitor
only reads Gmail and sends the 08:42 mail. Mock-up v3.1 approved 22:59 ("mockups are Fine, you can also proceed with the build").

## What this kit changes (the box)

| file | from → to | what |
|---|---|---|
| NEW `/root/assetapp/renewals_one.py` | — → see TO_PINS | the tables `renewal_item` / `renewal_mail` / `renewal_nag` in **assets.db**; the page sections *Found in your mail* · *Licences, documents and subscriptions* · *Staff documents*; **+ Add renewal**, **Mark renewed** (old row closed, new row opened — history kept); the token doors (`/renewals/one/api/due`, `/due/sent`, `/mail`, `/seed`); the count door for the home tile; the health page's `renewals_state.json` written from the list |
| `/root/assetapp/asset_register.py` (the SCAN APP's — PLANNED line v1810) | b668771c → a325d0f4 | `THRESHOLD_DEFAULT` 60 → 45; the `/renewals` template draws the new sections (4 anchors); the guarded mount block at the foot |
| `/root/portal/portal.py` (the parent's) | cb37c7fb → 9da49bd1 | every folder tile draws its inside tiles as **bold lines**; the Renewals line carries the red count (due within its lead time or overdue + mails to look at) |
| `/root/assetapp/renewals_one.token` | new, 0600 | the finance service's own `FINANCE_RENEWALS_TOKEN`, copied by the installer — no new secret, nothing pasted |
| crontab | + `45 2 * * * … renewals_one.py --state … # S890_RENEWALS_STATE` | the health file rewritten nightly from the list |

`finance_app.py` is NOT touched: its Renewals row keeps reading `renewals_state.json`, which the list now writes (only once the list has rows — until the seed the Janitor's own push stands). The push door stays for a week, then is retired (another kit).

## Rules built in
- **Numbers**: any run of 5+ digits and any vehicle registration is cut to its last 4 BEFORE storing — names, notes, mail excerpts (the Janitor cuts too).
- **Lead times** (D689 / D713 / S487): passport 365 · vehicle insurance 30 · PUC 7 · RC 45 · arms licence 45 · everything else 45. **Cadence**: daily inside 7 days, every 3 inside 21, weekly inside the lead time, a passport monthly before that; overdue kept 45 days.
- **Who**: the owner everything; a manager only Clinic / NK Pathology / Civic rows (Personal and Vehicle are his alone); reception never (the page's own gate).
- **A mail never changes a date by itself** — the one tap (Apply / Add as new / Not a renewal) does; a mail once answered is never shown again.
- **Staff documents** (the `expiries` rows of entity `staff`) reach the Renewals page — F-1493.

## Proven (18-Nov-2026, the device VM, python 3.10 + flask 3.1)
- `walk_s890_app.py` on the real scan app with the kit's files: **28/28**; CONTROL (the live files): 23 red, as it must be; 4 mutations (mask off · intake applies by itself · manager gate off · a renewed item still mailed) each caught.
- `walk_s890_portal.py`: **10/10**; CONTROL: 5 red, as it must be (node --check on the count script).
- `rehearse_s890.sh`: **13/13** (DRY · install · again · undo · undo again · red rollback at [4/6] · an open due door rolled back · no token in finance's settings · a drifted live file · a tampered kit · the lock held).
- `renewals_one.py --selfcheck`: OK (12).

## Install (his publish + one server line)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s890kit && cp -rp /root/deploy/repo/deploy_kits/S890_RENEWALS_ONE_LIST /tmp/s890kit && bash /tmp/s890kit/install_S890_RENEWALS_ONE_LIST.sh
```
Undo: `bash /tmp/s890kit/install_S890_RENEWALS_ONE_LIST.sh --undo`

## After the install (Claude, in the built-in browser; nothing for the owner)
1. Janitor / **Renewal_Nag.gs** replaced by `Renewal_Nag_v5.gs` (before/after sha256 recorded; the v4 text kept in the session papers for undo). The daily trigger `nagRenewals` stays.
2. Run **seedServerOnce()** once → the 24 + 6 typed rows on the server, numbers last 4 (the two S487 data fixes ride along). Read back: the count and every row's name (numbers already last 4) and expiry, against the Janitor's own renewalsExpiryCheck figures.
3. One morning in parallel (the 08:42 mail now from the server's list; compare with the day's `renewalsExpiryCheck` figures) → then `var RENEWALS = []; var ANNUAL_RENEWALS = [];` in Code.gs.
4. The Scan App chat told at the close (its file `asset_register.py`, its database).
