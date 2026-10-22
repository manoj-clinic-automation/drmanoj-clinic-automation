# S626_AMIR_PACK_STAYS — Amir's bank statements stay on his page (F-988)

*Kit S626 claimed by the Sanjeevni chat at session 338 (board `_numbers` v599 → v600, 22-Oct-2026 15:4x IST). Built, walked and
rehearsed in the chat itself. Project: **Sanjeevni**. Sanjeevni-owned file only.*

## What it does, in the owner's words

His board note of 22-Oct (point 5): *"amir needs bank statements to stay available to him till new month statement comes, current
ones vanished from his app."*

**Why they vanished:** Amir's page listed a month's pack (the Yes Bank and ICICI Sanjeevni statements, and the paid NEFT sheet) only
while it was ready **and not yet marked seen**. He tapped *Dekh liya* for September on 08-Oct 09:25, so the pack left his page at once.

**After this kit:** the newest month whose pack is ready stays on Amir's page, seen or not, until the next month's pack is ready
(the September statements stay until October's two statements are on the shelf). A seen month shows its links without the
*Dekh liya* button. A ready month he has not seen still shows with its button, exactly as before. The pack line never holds up his
day (it was never one of his Marg tasks, and still is not).

## The change

| file | from | to | what |
|---|---|---|---|
| `/root/finance/amir_day.py` | `1169a3d6` | `2c99c29e` | `_s446_packs` returns `(month, seen)`; the newest ready month always kept. The pack row draws the button only for an unseen month. |

Nothing else: no database write, no setting, no crontab line, no other file. `packs.py` (the parent's) and `supplier_msg.py` are read
only. One restart of clinic-finance.

## Install — the owner's one server line (after his publish)

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S626_AMIR_PACK_STAYS/install_S626_AMIR_PACK_STAYS.sh
```

Order: gates (08:02–23:49 IST, SUMS, KIT_ID) → the build lock → ALREADY INSTALLED → the FROM pin → build from the live bytes →
compile (both pythons) → the walk on scratch copies (OLD must be red on F-988, NEW 12/0, including one check on a copy of the live
database) → backup `amir_day.py.bak_S626_1169a3d6` → placed and read back → one restart → healthz 200, `/finance/amir` 302 → journal
clean → `S626_AMIR_PACK_STAYS: DONE`. `DRY=1` before `bash` stops before the backup.

## Undo

```
\cp -p /root/finance/amir_day.py.bak_S626_1169a3d6 /root/finance/amir_day.py && systemctl restart clinic-finance
```
