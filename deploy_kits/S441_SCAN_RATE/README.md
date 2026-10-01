# S441_SCAN_RATE — the scan flow without waiting, the after-the-fact checks, the shared login's name, the compact rate page

**Session 287 (parent), 01-Oct-2026 · D643 · F-665 · F-666 · F-667 · plan `S286_NEXT_BUILD_PLAN.md` §A.**

One line on the VPS (the owner's):

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S441_SCAN_RATE/install_S441_SCAN_RATE.sh

## What staff see
- Bill scan: every photo is a page by itself; one **Save**; a small **Retake** under each page. The stamp shows at once,
  big ("kaagaz par likho"); the camera stays ready for the next bill. A slow upload retries by itself (about a minute) and
  can never make a second bill (one `client_token` per Save). **PDF / file** sends a WhatsApp / e-mail bill as it is.
- The shared **Reception** login: "Kaun kaam kar raha hai?" once — Shivani, Alisha, Darpan, Sukhveer, Shavez — remembered
  until 30 minutes idle or **badlo**. Every stamp, order sent and arrival marked carries the name. Reception can now send orders.
- Purchase orders → Scan ka kaam: a new group **Dobara scan? / Galat lane?** (Shavez and reception both see it; the first
  answer settles it; "Jawab ho gaye" shows who answered).

## What the server does after the fact (`/root/shared/scan_checks_s441.py`)
- A forgotten page (same person, within 5 minutes, same bill number or no bill header, a different picture) joins its bill;
  the PDF is merged into a new file (both originals kept). Only for scans made from 01-Oct (history keeps its pages).
- A sure double (same supplier, same bill-number tail, amount within 2% — S439's rules, copied in and proven equal on every
  name and number on the box) is set aside: `status='rejected'`, `dup_of`, kept, out of counts and packs. The scan S439
  linked to a Marg bill is the one kept; an approved bill is never set aside by a rule (asked instead).
- A near match, or a Marg pharmacy supplier scanned in the clinic lane, becomes one question.

## The owner's rate page (`/finance/clinic/sheets`)
One short line per item; tap to edit; consumables folded; groups and sections fold; every save in place; an X-ray save stays
on the X-ray view (F-665: `_back()` dropped `?kind=xray`).

## Files
See the installer header: seven full files, FROM → TO pins, `.bak_S441_<from8>` beside each, database backups first.
`porders.py` / `porders.html` are the Sanjeevni chat's, declared on `board/_numbers` (the S286 PLANNED line) before building.
