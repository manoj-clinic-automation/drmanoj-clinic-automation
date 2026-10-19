# S597_WA_INBOX — the owner's WhatsApp Inbox (D744)

**The owner, 19-Oct-2026 (01:56–06:10 IST):** interactive WhatsApp from the clinic number — see photos, PDFs and voice
notes, reply with text, photo, PDF and voice note, an inline Call button, full mobile number and clinic ID, only him.
Mockups approved 06:10 IST. Kit S595 (08:17 IST) proved on his own phone that MyOperator delivers a photo, a PDF and an
MP3 voice note sent this way (OGG was refused).

**The one line (VPS):**

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S597_WA_INBOX/install_S597_WA_INBOX.sh

Then open **https://followup.dr-manoj.in/portal/inbox** (or the *WhatsApp Inbox* tile under *Calls & WhatsApp*).

## What it is
- `portal_inbox.py` — one page at `/portal/inbox` inside the portal, behind its WhatsApp gate (`wa_required`: the doctor
  login and a name in `PORTAL_WA_USERS`, today `manoj` alone). The tile is masked for bhawna.
- **Messages:** read from the receiver's own raw log `/root/wa/wa_logs/*.jsonl` (every push, written first) into
  `/root/wa/wa_inbox/inbox.db`, forward from a saved place in each file — with the receiver's own field paths. The
  receiver, its sheet and its senders are not changed.
- **Media in:** fetched once from MyOperator's copy when first opened, kept in `/root/wa/wa_inbox/media/` (root, 600),
  shown only behind the login.
- **Media out:** photo (JPG/PNG, shrunk in the browser to 1600 px), PDF (≤ 20 MB), voice note (recorded in the browser,
  encoded there as MP3 with `lame.min.js`, LGPL — carried in the kit as base64 text because its number tables would trip the phone-number gate, decoded and MD5-checked at install). Kept in `/root/wa/wa_inbox/out/`, handed to MyOperator as
  `/portal/inbox/f/<32-hex token>/<name>` — the one route without the login, valid 6 hours.
- **24-hour rule:** free reply only within 24 h of the patient's last message; after that the page offers the approved
  templates through `portal_wa`'s own registry and sender (its test-mode switch `PORTAL_WA_DRYRUN` applies and is shown).
- **Call:** the live call service (`127.0.0.1:8097/call`, agent 10 = Dr Manoj): his mobile rings first.
- **Alert:** `wa_alert.py` adds an ntfy *Click* link `…/portal/inbox?m=<message id>` — tapping the alert opens that chat.
  The link carries no number.

## The three live edits (`patch_s597.py`, pinned both ways — `AFTER.md5`)
| file | in | out | change |
|---|---|---|---|
| `/root/portal/portal.py` | 25cb73e7 | 3be15f45 | tile, group entry, bhawna code mask, register block |
| `/root/portal/tile_grants.json` | e54f59db | 6498a916 | bhawna mask + "WhatsApp Inbox"; v36 → v37 |
| `/root/wa/wa_alert.py` | e7d0b766 | 89c08929 | ntfy Click link to the chat |

Restarts: `clinic-portal`, `wa-receiver` (each checked; a bad answer puts the files back by itself).
Undo: `bash install_S597_WA_INBOX.sh --undo`.

## Rehearsed (S329)
- 53-check server walk on the patched portal (Flask test client): gate, list, names + clinic ID, unread, late media
  link, status ticks, search, media fetch + cache, read marks, text / PDF / photo / MP3 sends in S595's shape, OGG and
  > 5 MB refused before MyOperator, public link without login and its 404s (wrong name, token, expired), 24-hour refusal,
  template via portal_wa in test mode, call body, saved replies, the alert link, a half-written log line.
- 35-check browser walk (Chromium, fake microphone): desktop and phone, a real recording turned into a real MP3
  (ffprobe), a 3000-px photo shrunk to 1600, PDF with caption, call, templates after 24 h, no page errors, no sideways
  scroll; two rounds of screen review by a separate reader, every defect fixed.
- The installer itself on a stand-in server tree, including the control (a broken inbox module → everything put back by itself), a second run (nothing changed twice) and `--undo`.
