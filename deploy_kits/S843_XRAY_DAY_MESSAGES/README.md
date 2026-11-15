# S843_XRAY_DAY_MESSAGES — the 9:30 am and 7 pm X-ray messages (the parent, S469, 14-Nov-2026) — D979 item 6

**His word.** 13-Nov 19:27–19:34 IST (S450 study §I point 2): reception gets yesterday's X-ray list at 9:30 am and a
confirmation in the evening after the upload ("all N in" / "n of N in, the rest named"); he gets the evening line too; counts on
the lock screen, names inside the portal; nothing on a day with no X-ray and no blood test; the 3 / 6 pm notice stays.
The wording: the artboard "The messages — final wording (S469)" on https://claude.ai/artifact/W5TAwHRWP5zFBpN9HtqFhB —
"your mockups seem fine to me" (22:03 IST 14-Nov), with his note that the pages are reached through the portal tiles
(the tap opens the existing Check karein pages, which are the tiles' own pages).

**The change.** One NEW file and two cron lines; nothing else on the box moves.
- `/root/finance/xray_day_messages.py` (md5 in `TO_PINS.md5`) — `morning` and `evening`, the venv's python:
  - `30 9 * * *` **morning** → Reception, Shivani, Alisha: `check_screens.kal_card(day_strip)` — the newest X-ray day before
    today: "📷 X-ray 13 Nov: 8 mein se 6 ki photo aa gayi" / "2 baaki — aaj 3 baje tak upload kijiye. Pichhle 7 din se 1 aur
    baaki." or "✅ … sab 8 ki photo aa gayi". Silent when that day is not yesterday and nothing is baaki. Tap → `/finance/checks`.
  - `0 19 * * *` **evening** → the same three: "Aaj ki upload" — the X-rays due by 3 pm today (yesterday evening's and its
    this morning's; a Docterz-only line by its Docterz shift), filed or on their way vs the rest; silent when none was due. → him (`manoj`):
    "Records today: X-rays n of N filed · Blood n of N in" with pending / photo needs a check / blood not in yet /
    Check karein questions open (`check_screens.counts`: waiting pictures + likely-wrong lab IDs + not-in-Docterz X-rays);
    silent with no X-ray due and no blood test. Both silent on a day with no X-ray and no blood test (a closed Sunday); the
    morning is silent on Sundays (Monday's carries Saturday). Tap → `/finance/records/xray-check`.
  - Every list and state is check_screens' / records' own (the due rule is never copied, F-1384). The database is opened
    read-only. Counts only in the notification, the state file and the log — no name, number or ID anywhere.
  - The notification slot is the 3 / 6 pm notice's (`tag xray-photo`): the newest replaces the older on the phone.
  - Off: `/root/finance/_off/ALL_OFF` or `/root/finance/_off/xray_day_messages`. State `/root/finance/xray_day_messages_state.json`,
    log `/root/finance/xray_day_messages.log`.

**Install (one line on the server):**
`cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s843kit && cp -rp /root/deploy/repo/deploy_kits/S843_XRAY_DAY_MESSAGES /tmp/s843kit && bash /tmp/s843kit/install_S843_XRAY_DAY_MESSAGES.sh`
Undo: `bash /tmp/s843kit/install_S843_XRAY_DAY_MESSAGES.sh --undo`. `DRY=1` before `bash`: every gate, nothing written.

**Proof.** `walk_s843.py` (42 checks on made-up data) and `--control` (five broken copies go red: 'not due' counted as in,
today's evening X-rays counted due, the error's text kept, Shavez added to reception, the switch ignored); `--live` on the
14-Nov database copy: the evening counts equal records' own XRAY_DUE (Docterz-only lines by their shift) + the 2-day photo
window on seven days, and the copy's md5 does not move. The
installer runs the walk, the control and both dry runs on the live database before placing anything. Cold review
(S469): SAFE TO INSTALL; its two MEDIUM and the LOW points 3-8 are built in (v2, `S843 2`).
