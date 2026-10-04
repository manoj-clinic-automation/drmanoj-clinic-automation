# S472_MAHINE_KA_KAAM — Shavez's "Mahine ka kaam", a better flow (session 293, 04-Oct-2026)

**The owner's words (04-Oct):** "the Shavez Mahine ka kaam etc also needs a better flow". Chained on `S471_PACKS_SEPTEMBER`.

| where | from → to | what |
|---|---|---|
| `/root/finance/packs.py` | 6738d65d → 6099b525 | a **due day** per item (column `packs_item.due_day`; by kind when unset: Docterz the 1st, statements/scans the 5th, NEFT the 7th, hand-overs and the accountant's things the 10th, the petty book the 3rd; the owner's own day wins, set on his rename tap) · **late / due today** on every row · the tile's line `/finance/packs/api/checklist/line` ('N kaam baaki · M late · aaj: …') · a **hand-over ticked with a photo** (multipart on the same tick door; jpeg/png, 8 MB; kept under the packs folder as `handover/<month>/<item>_<stamp>.jpg`; served at `/finance/packs/handover/<month>/<name>` to staff and the owner) |
| `/root/finance/packs_checklist.html` | 12ac3f27 → 74598ba7 | **Aaj ka kaam** first (due today or late); 'N tak' on every row, late in red; **Ho gaya — tick karein**; a hand-over row offers **📷 Photo ke saath ho gaya** (the phone's camera) and *bina photo* behind one confirmation; a done row shows who, when and *photo ✓* |
| `/root/portal/portal.py` | 1a9fb99d → d9b7685f | the **Mahine ka kaam** tile carries the live line (fail-soft; red when late) |

**No WhatsApp nudge:** a staff message outside a patient's 24-hour window needs an approved template, and none exists for this;
the tile is where he already looks every day. The owner's packs page reads the same API: its Shavez section gains the late/due words.
Not touched: the send, the shelf, every other tile, the Sanjeevni files.

## Proven — `walk_s472.py`, hermetic (F-709)
packs.py beside the box's readers in `/tmp`, an EMPTY database, a scratch packs folder, a throwaway Flask app with a made-up staff
login. 35 checks: the due days by kind; late and due-today against a fixed today; the tile's line; a hand-over ticked WITH a photo
through the real door (kept under the scratch folder, shown on the row, served by the photo door; a bad name 404; a .txt refused
silently with the tick standing; a JSON tick without a photo still works); the owner's day wins; the pages' words; SHOWN on the
old file that the checklist knew no due day. Offline 04-Oct: `WALK_S472 GREEN 35 checks, 0 fail`.

## Install (the owner's one line, AFTER S471; the lock F-694; DRY=1 places nothing)
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S472_MAHINE_KA_KAAM/install_S472_MAHINE_KA_KAAM.sh
```
Red after placing → the three files are put back. Backups `.bak_S472_<from8>` beside each.
