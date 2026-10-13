# S544_RECEPTION_FIVE — reception captures only; Personal expenses with Dr MK / Dr Bhawna; Dr MK Clinic Equipment (D719 kit a; F-891)

*Scan App project, S314, 13-Oct-2026. The owner's D719 (12-Oct 06:35; 13-Oct 05:48 → 06:15). The staff screen follows the
mock-up (artifact VPhYKjuNqyLHGmcxKwbLWi, "Reception scan — five buttons") and is **installed OFF**. Built by BUILD_NORM_v1
(D704). Installs after S545 or before it — the two kits touch different files.*

## What the kit does
**Reception's intake (staff; behind the owner's switch, OFF at install):** *Yeh kaagaz kiska hai?* — four big buttons,
**Clinic · Pharmacy · NK Pathology · Other document**, each with a one-line hint in Roman Hinglish; the **CHALLAN** button
as before under them (the fifth). The person's own default lane is lit (nobody opens on Personal expense); one tap changes it; the lane line under the
buttons says what will be sent (*· mahina badlo* opens the month). **Dr MK expense is gone from reception** — not a
button, not in the old drop-down; a reception scan that still arrives marked for it (an old open page) lands on the
Clinic lane (the server decides, not the page).

**The owner and the managers (Shavez):** the same four, in English for the owner, plus **Personal expense** with
**Dr MK / Dr Bhawna** under it; nothing chosen = Dr MK. Stored on the paper (`bills.pe_who`: `bhawna` or empty).

**The lane `owner_expense` reads "Personal expense" everywhere** (its key, its rows, the accountants' pack's lane are
unchanged — the pack still takes the lane). On the **papers page**: a fold **Personal expenses — Dr MK n · Dr Bhawna n**
(the owner and the managers), each paper with its warranty; on **each personal expense's own page**: *Personal expense —
whose?* Dr MK / Dr Bhawna (one tap, audited `pe_who`), the warranty card as before. The stand row and the Renewals card
say Personal expenses. The two Dr MK expense papers already scanned are carried in as Dr MK, with their warranties.

**The asset register:** *Medical Equipment* → **Dr MK Clinic Equipment** — the list, and every asset already in it
(the app's own migration at every start, idempotent; without it an edit would have dropped those assets to Other).

**F-891 repaired:** a paper in the section **Personal** (the owner's alone, D710) is now closed to managers on the
bill page, its file and its picture, the edit page and every checker door that looks a bill up (approve, reject,
re-read, month, lane, duplicate), the bills list and its search, a supplier's purchase history, the new Personal
expenses fold and its whose? door — not only on the papers page (the independent read found the fold and the doors).

**The switch:** `/scanapp/admin` — card *Bill intake — reception's lane buttons* (setting `scan.lanes5`). OFF = the
intake exactly as before (only the words *Personal expense* in its drop-down; every login keeps its own default).

**The accountants' pack (D721, the owner 14:13 IST 13-Oct):** a paper marked Dr Bhawna goes into her own expense file,
the pack's item 8.3 — kit S548 (the parent's `packs.py`, PLANNED on the board); 8.2 keeps Dr MK's.

## Files
| file | FROM (pinned) | TO |
|---|---|---|
| `/root/assetapp/asset_register.py` | `35f9e823` (S532) | `PIN_TO_asset_register.txt` — backup `.bak_S544_35f9e823` |
| `/root/assetapp/clinic_papers.py` | `476e157c` (S532.1) | `PIN_TO_clinic_papers.txt` (S544.1) — backup `.bak_S544_476e157c` |

`make_s544.py` (25 + 15 counted edits; refuses any other FROM) · `install_s544.sh` · `walk_s544.py` · `walk/` (the
intake page renderer and the Chromium tap walk, the results). Database: one additive column `bills.pe_who`; the
category text on the assets in Medical Equipment. `scanner_widget.js` is not touched.

## Proven (walk/walk_results.txt)
- **The app walk: 41 of 41** on the built files — the switch OFF/ON/OFF, reception's four (no Personal expense anywhere,
  a stale Personal expense scan lands on Clinic), the owner's and the manager's Personal expense, Dr MK / Dr Bhawna at
  intake and on the paper's page (audited; reception refused; a non-expense refused), the papers page fold, F-891 on
  every door (F1–F8 on rows written straight in, W27–W29 through the intake), the category rename. **The control**
  on the live files: 21 red (F-891's checks among them).
- **Chromium, 390 × 844, switch ON: 19 of 19** — each tap sets what the scanner will send (lane, the half-A4 hint on
  Pharmacy, the basic form), the lane line in the button's own words, Challan works beside them, Dr MK / Dr Bhawna for the owner only, buttons ≥ 44 px, no
  sideways scroll, no script error.
- **The installer**, rehearsed on a made-up root with a running copy of the app: DONE · ALREADY INSTALLED · health red
  (40 s of tries) → both files **and the category name** restored · a wrong FROM → refused. The database read-back is a
  gate: no column or an asset left in Medical Equipment → restored.
- **An independent read** (a reviewer who had not seen the build): one blocker (the fold showed a manager a Personal
  paper) and two corrections (the whose? door; the owner's default while OFF) — all three taken in and walked.
- On the box the installer repeats the walk on a **copy of the live database** (under its own home, removed after).

## Install (the owner's one line, after the publish)
`cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S544_RECEPTION_FIVE/install_s544.sh`

Order: gates → pins → rebuild on the box → walk + control → backups (both files, the database) → place → restart
`assetapp` only → health (red → restored by itself) → the database read back → the words. Staff see nothing until the
owner's tap on `/scanapp/admin`.

## Undo (one line)
`cp -p /root/assetapp/asset_register.py.bak_S544_35f9e823 /root/assetapp/asset_register.py && cp -p /root/assetapp/clinic_papers.py.bak_S544_476e157c /root/assetapp/clinic_papers.py && python3 -c "import sqlite3; d=sqlite3.connect('/root/assetapp/assets.db'); d.execute(\"UPDATE assets SET category='Medical Equipment' WHERE category='Dr MK Clinic Equipment'\"); d.commit()" && systemctl restart assetapp`
